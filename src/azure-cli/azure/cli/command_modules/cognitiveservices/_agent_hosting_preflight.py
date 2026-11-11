# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import hashlib
import re
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Optional

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id, resource_id
from azure.cli.core.azclierror import (
    InvalidArgumentValueError, RequiredArgumentMissingError, ValidationError,
)
from knack.log import get_logger

from ._client_factory import get_agent_hosting_clients, get_cognitiveservices_management_client

if TYPE_CHECKING:
    from azure.mgmt.msi.models import Identity
    from azure.mgmt.storage.models import StorageAccount


logger = get_logger(__name__)


_RESOURCE_TYPES = {
    'cluster': 'Microsoft.ContainerService/managedClusters',
    'storage': 'Microsoft.Storage/storageAccounts',
    'management_identity': 'Microsoft.ManagedIdentity/userAssignedIdentities',
    'workload_identity': 'Microsoft.ManagedIdentity/userAssignedIdentities',
}


_OPTION_NAMES = {
    'cluster': '--agent-hosting-cluster', 'storage': '--agent-hosting-storage',
    'management_identity': '--agent-hosting-management-identity',
    'workload_identity': '--agent-hosting-workload-identity',
}


_ROLE_IDS = {
    'Reader': 'acdd72a7-3385-48ef-bd42-f606fba81ae7',
    'Kubernetes Extension Contributor': '85cb6faf-e071-4c9b-8136-154b5a04f717',
    'Managed Identity Federated Identity Credential Contributor': '7e559ce2-48d7-4b27-9128-fa1b247f1308',
    'Storage Blob Data Contributor': 'ba92f5b4-2d11-453d-a403-e96b0029c9fe',
    'Storage Blob Data Owner': 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b',
    'Owner': '8e3af657-a8ff-443c-a75c-2fe8c4bcb635',
    'Contributor': 'b24988ac-6180-42a0-ab88-20f7382dd24c',
}


@dataclass(frozen=True)
class HostingRequest:
    account_id: str
    location: str
    cluster: str
    storage: Optional[str] = None
    management_identity: Optional[str] = None
    workload_identity: Optional[str] = None


@dataclass(frozen=True)
class Grant:
    name: str
    identity_id: str
    scope: str
    role_id: str


# Keep the existing-account fast path explicit instead of inferring it from empty evidence fields.
@dataclass(frozen=True)
class PreflightResult:  # pylint: disable=too-many-instance-attributes
    resources: HostingRequest
    management_identity: Optional['Identity']
    workload_identity: Optional['Identity']
    storage: Optional['StorageAccount']
    storage_sku: Optional[str] = None
    grants: tuple[Grant, ...] = ()
    checks: tuple = ()
    existing_account: bool = False


def build_request(cmd, resource_group_name, account_name, location, **inputs):
    from azure.cli.core.commands.client_factory import get_subscription_id
    if not isinstance(account_name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{1,63}', account_name):
        raise InvalidArgumentValueError(
            '--name must be 2-64 characters, start with a letter or digit, and contain only '
            'letters, digits, underscores or hyphens.')
    account_id = resource_id(subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
                             namespace='Microsoft.CognitiveServices', type='accounts', name=account_name)
    return HostingRequest(account_id, location, **inputs)


def preflight(cli_ctx, request, *, kind=None, custom_domain=None):
    resources = _resolve_resources(request)
    subscription = parse_resource_id(request.account_id)['subscription'].lower()
    if any(parse_resource_id(arm_id)['subscription'].lower() != subscription
           for arm_id in (resources.cluster, resources.storage)):
        raise InvalidArgumentValueError(
            'The Account, AKS cluster and Storage account must be in the same subscription.')
    checks, clients = [], {}
    account = parse_resource_id(request.account_id)
    cognitive_client = get_cognitiveservices_management_client(cli_ctx)
    existing_account = _read_account(cognitive_client, account)
    if existing_account is not None:
        _validate_existing_account(existing_account, request, resources)
        if custom_domain:
            _check_domain(cognitive_client, existing_account, custom_domain, kind)
        return PreflightResult(resources, None, None, None, existing_account=True)
    account_clients = _clients(cli_ctx, request.account_id, clients)
    if not account_clients.resource.resource_groups.check_existence(account['resource_group']):
        raise ValidationError(
            f"Resource group '{account['resource_group']}' does not exist. Create it before retrying.")
    _report(checks, 'Resource group', request.account_id, True, 'Exists', 'Existing resource group', 'None')
    if custom_domain:
        _check_domain(cognitive_client, None, custom_domain, kind)
    with _read_check(checks, 'Tenants', request.account_id):
        _check_tenants(cli_ctx, clients, resources, checks)
    _report(checks, 'Distinct identities', request.account_id,
            resources.management_identity.lower() != resources.workload_identity.lower(),
            f'{resources.management_identity}; {resources.workload_identity}',
            'Different management and workload identities', 'Supply distinct identities.')
    cluster = None
    with _read_check(checks, 'AKS cluster', resources.cluster):
        cluster_parts = parse_resource_id(resources.cluster)
        cluster = _clients(cli_ctx, resources.cluster, clients).aks.managed_clusters.get(
            cluster_parts['resource_group'], cluster_parts['name'])
        _check_cluster(cluster, resources.cluster, request.location, checks)
    management = _read_identity(_clients(cli_ctx, resources.management_identity, clients).identity,
                                resources.management_identity, request.management_identity is not None, checks)
    workload = _read_identity(_clients(cli_ctx, resources.workload_identity, clients).identity,
                              resources.workload_identity, request.workload_identity is not None, checks,
                              workload=True)
    storage, storage_sku = _read_storage(
        _clients(cli_ctx, resources.storage, clients).storage, resources.storage,
        request.storage is not None, request.location, checks)
    with _read_check(checks, 'Node pools', resources.cluster):
        cluster_clients = _clients(cli_ctx, resources.cluster, clients)
        if cluster is not None:
            _check_pools(cluster_clients.aks, cluster, resources.cluster, checks)
    checked = PreflightResult(resources, management, workload, storage, storage_sku)
    grants = ()
    with _read_check(checks, 'Permissions', request.account_id):
        grants = _check_grants(cli_ctx, clients, request, checked, checks)
    if any(check['mandatory'] and check['status'] in ('FAIL', 'UNVERIFIED') for check in checks):
        raise ValidationError('BYO AKS preflight failed. No Azure resources were written. '
                              'Resolve the reported checks and retry.')
    return replace(checked, grants=tuple(grants), checks=tuple(checks))


def _read_account(client, account):
    try:
        return client.accounts.get(account['resource_group'], account['name'])
    except ResourceNotFoundError:
        return None


def _validate_existing_account(existing, request, resources):
    properties = getattr(existing, 'properties', None)
    configurations = getattr(properties, 'agent_hosting_configurations', None) if properties else None
    if not configurations:
        raise ValidationError(
            f'Account {request.account_id} already exists without agent hosting. '
            'Agent hosting can only be configured when the Account is created.')
    if _normalize_location(getattr(existing, 'location', None)) != _normalize_location(request.location):
        raise ValidationError(
            f'Account {request.account_id} already exists in location {getattr(existing, "location", None)}. '
            f'Use the existing location instead of {request.location}.')
    if not isinstance(configurations, (list, tuple)) or len(configurations) != 1 or configurations[0] is None:
        raise ValidationError(
            f'Account {request.account_id} has an incompatible agent hosting configuration. '
            'Updating or removing agentHostingConfigurations is not supported.')

    expected = {
        'name': 'default',
        'hosting_type': 'ManagedCluster',
        'cluster_resource_id': resources.cluster,
        'storage_account_resource_id': resources.storage,
        'hosting_management_identity_resource_id': resources.management_identity,
        'workload_identity_resource_id': resources.workload_identity,
    }
    configuration = configurations[0]
    resource_ids = {
        'cluster_resource_id',
        'storage_account_resource_id',
        'hosting_management_identity_resource_id',
        'workload_identity_resource_id',
    }
    mismatches = []
    for field, expected_value in expected.items():
        actual = getattr(configuration, field, None)
        if field in resource_ids:
            matches = (
                isinstance(actual, str) and
                _normalize_resource_id(actual) == _normalize_resource_id(expected_value)
            )
        else:
            matches = actual == expected_value
        if not matches:
            mismatches.append(field)
    if mismatches:
        raise ValidationError(
            f'Account {request.account_id} has an incompatible agent hosting configuration '
            f'({", ".join(mismatches)}). Updating or removing agentHostingConfigurations is not supported.')


def _normalize_resource_id(value):
    return value.strip().rstrip('/').lower()


def _check_domain(client, existing, custom_domain, kind):
    from azure.mgmt.cognitiveservices.models import CheckDomainAvailabilityParameter
    current = existing.properties.custom_sub_domain_name if existing and existing.properties else None
    if current and current.lower() == custom_domain.lower():
        return
    availability = client.check_domain_availability(CheckDomainAvailabilityParameter(
        subdomain_name=custom_domain, type='Microsoft.CognitiveServices/accounts', kind=kind))
    if availability.is_subdomain_available is not True:
        raise ValidationError(
            f"Custom domain '{custom_domain}' is not available: "
            f"{availability.reason or 'The service did not confirm availability.'}")


def _clients(cli_ctx, arm_id, cache):
    subscription = parse_resource_id(arm_id)['subscription']
    key = subscription.lower()
    if key not in cache:
        cache[key] = get_agent_hosting_clients(cli_ctx, subscription)
    return cache[key]


def validate_resource_ids(**inputs):
    for key, value in inputs.items():
        if value is None:
            continue
        option = _OPTION_NAMES[key]
        if not isinstance(value, str) or not value.strip() or not is_valid_resource_id(value):
            raise InvalidArgumentValueError(f'{option} must be a fully qualified Azure resource ID.')
        parts = parse_resource_id(value)
        actual = '/'.join(filter(None, (parts.get('namespace'), parts.get('type'),
                                        parts.get('child_type_1')))).lower()
        if (actual != _RESOURCE_TYPES[key].lower() or not parts.get('subscription') or
                not parts.get('resource_group') or parts.get('child_type_2') or parts.get('child_namespace_1')):
            raise InvalidArgumentValueError(f'{option} must identify a {_RESOURCE_TYPES[key]} resource.')
    hosting = [inputs.get(key) for key in ('cluster', 'storage', 'management_identity', 'workload_identity')]
    if any(value is not None for value in hosting) and inputs.get('cluster') is None:
        raise RequiredArgumentMissingError('--agent-hosting-cluster is required when configuring agent hosting.')
    management, workload = inputs.get('management_identity'), inputs.get('workload_identity')
    if management is not None and workload is not None and management.lower() == workload.lower():
        raise InvalidArgumentValueError('Hosting-management and workload identities must be different resources.')


def _names(subscription, group, account):
    account_id = resource_id(subscription=subscription, resource_group=group,
                             namespace='Microsoft.CognitiveServices', type='accounts', name=account)
    token = hashlib.sha256(account_id.lower().encode('utf-8')).hexdigest()[:10]
    return {
        'storage': re.sub('[^a-z0-9]', '', account.lower())[:14] + token,
        'management_identity': account.lower() + '-hosting-mi', 'workload_identity': account.lower() + '-workload-mi',
    }


def _resolve_resources(request):
    account = parse_resource_id(request.account_id)
    names = _names(account['subscription'], account['resource_group'], account['name'])

    def identity_id(name):
        return resource_id(subscription=account['subscription'], resource_group=account['resource_group'],
                           namespace='Microsoft.ManagedIdentity', type='userAssignedIdentities', name=name)

    storage_id = resource_id(subscription=account['subscription'], resource_group=account['resource_group'],
                             namespace='Microsoft.Storage', type='storageAccounts', name=names['storage'])
    return replace(request, storage=request.storage if request.storage is not None else storage_id,
                   management_identity=request.management_identity if request.management_identity is not None
                   else identity_id(names['management_identity']),
                   workload_identity=request.workload_identity if request.workload_identity is not None
                   else identity_id(names['workload_identity']))


def _report(checks, name, scope, passed, observed, expected, remediation, mandatory=True):
    status = passed if isinstance(passed, str) else ('PASS' if passed else 'FAIL')
    checks.append({'name': name, 'scope': scope, 'status': status, 'mandatory': mandatory,
                   'observed': observed, 'expected': expected, 'remediation': remediation})
    if isinstance(observed, (list, tuple)):
        observed = '\n    ' + '\n    '.join(str(item) for item in observed)
    elif isinstance(observed, dict):
        observed = '\n    ' + '\n    '.join(f'{key}: {value}' for key, value in observed.items())
    if status in ('FAIL', 'UNVERIFIED'):
        logger.warning('Preflight check failed: %s\n  Scope: %s\n  Details: %s\n  Requirement: %s\n  Action: %s',
                       name, scope, observed, expected, remediation)
    elif status == 'NOT_APPLICABLE':
        logger.info('Not applicable: %s [%s]: observed=%s; note=%s', name, scope, observed, remediation)
    else:
        recommendation = '' if remediation == 'None' else f'; recommendation={remediation}'
        logger.info('Validated %s [%s]: observed=%s; expected=%s%s',
                    name, scope, observed, expected, recommendation)


@contextmanager
def _read_check(checks, name, scope):
    try:
        yield
    except ResourceNotFoundError:
        _report(checks, name, scope, False, 'Resource not found', 'Existing readable resource',
                'Supply an existing resource ID.')
    except AzureError as error:
        _report(checks, name, scope, 'UNVERIFIED', str(error), 'Readable prerequisite evidence',
                'Resolve the reported Azure error and retry.')


def _check_tenants(cli_ctx, clients, resources, checks):
    references = (resources.account_id, resources.cluster, resources.management_identity,
                  resources.workload_identity, resources.storage)
    subscriptions = {parse_resource_id(value)['subscription'].lower() for value in references if value is not None}
    tenant = None
    for subscription in sorted(subscriptions):
        client = _clients(cli_ctx, f'/subscriptions/{subscription}', clients).subscription
        current = client.subscriptions.get(subscription).tenant_id
        if tenant is None:
            tenant = current
        _report(checks, 'Tenant', subscription, bool(current and tenant and current.lower() == tenant.lower()),
                current, tenant or 'Readable tenant ID', 'Use subscriptions in the same tenant.')


def _missing_identity_fields(identity, workload=False):
    fields = {'principalId': identity.principal_id}
    if workload:
        fields.update(clientId=identity.client_id, tenantId=identity.tenant_id)
    return [name for name, value in fields.items() if value is None or not str(value).strip()]


def _read_identity(client, arm_id, supplied, checks, workload=False):
    parts = parse_resource_id(arm_id)
    with _read_check(checks, 'Identity', arm_id):
        try:
            identity = client.user_assigned_identities.get(parts['resource_group'], parts['name'])
        except ResourceNotFoundError:
            _report(checks, 'Identity', arm_id, not supplied, 'Not found',
                    'Existing supplied resource' if supplied else 'Planned creation',
                    'Supply an existing resource ID.')
            return None
        missing = _missing_identity_fields(identity, workload)
        _report(checks, 'Identity metadata', arm_id, not missing, f'Missing: {missing}' if missing else 'Available',
                'principalId, clientId and tenantId' if workload else 'principalId',
                'Wait for identity provisioning to complete.')
        return identity
    return None


def _read_storage(client, arm_id, supplied, location, checks):
    parts = parse_resource_id(arm_id)
    storage, storage_sku = None, None
    with _read_check(checks, 'Storage', arm_id):
        try:
            storage = client.storage_accounts.get_properties(parts['resource_group'], parts['name'])
        except ResourceNotFoundError:
            if supplied:
                _report(checks, 'Storage', arm_id, False, 'Not found', 'Existing supplied resource',
                        'Supply an existing resource ID.')
                return None, None
        if storage is not None:
            _check_storage(storage, arm_id, location, checks)
        elif not supplied:
            availability = client.storage_accounts.check_name_availability({
                'name': parts['name'], 'type': 'Microsoft.Storage/storageAccounts'})
            _report(checks, 'Storage name availability', arm_id, availability.name_available is True,
                    availability.message or availability.name_available, 'Available deterministic Storage name',
                    'Supply an existing Storage account if the generated name is unavailable.')
            if availability.name_available is True:
                storage_sku = _select_storage_sku(client, location)
                _report(checks, 'Storage configuration', arm_id, True, storage_sku,
                        'Planned StorageV2/Hot; prefer ZRS and use LRS when unavailable', 'None')
    return storage, storage_sku


def _normalize_location(value):
    return re.sub(r'\s', '', value or '').lower()


def _enum_value(value):
    return getattr(value, 'value', value)


def _select_storage_sku(client, location):
    target = _normalize_location(location)
    for sku in client.skus.list():
        if _enum_value(sku.name) != 'Standard_ZRS' or _enum_value(sku.kind) != 'StorageV2':
            continue
        if target not in {_normalize_location(value) for value in sku.locations or []}:
            continue
        restricted = any(
            str(_enum_value(item.type)).lower() == 'location' and
            (not item.values_property or
             target in {_normalize_location(value) for value in item.values_property})
            for item in sku.restrictions or [])
        if not restricted:
            return 'Standard_ZRS'
    return 'Standard_LRS'


def _version_at_least(value, baseline):
    if not isinstance(value, str) or not re.fullmatch(r'\d+(?:\.\d+)*', value):
        return False
    current, expected = [tuple(int(part) for part in version.split('.')) for version in (value, baseline)]
    length = max(len(current), len(expected))
    return current + (0,) * (length - len(current)) >= expected + (0,) * (length - len(expected))


def _image_supported(value):
    prefix = 'AKSAzureLinux-V3katagen2-'
    return (isinstance(value, str) and value.startswith(prefix) and
            _version_at_least(value[len(prefix):], '202608.14.0'))


def _check_cluster(cluster, scope, location, checks):
    if cluster.properties is None:
        _report(checks, 'AKS cluster', scope, 'UNVERIFIED', 'Missing properties', 'Readable cluster properties',
                'Read a fully provisioned cluster.')
        return
    properties = cluster.properties
    network, oidc, security = properties.network_profile, properties.oidc_issuer_profile, properties.security_profile
    sku, identity = cluster.sku, cluster.identity
    kubelet = next((value for key, value in (properties.identity_profile or {}).items()
                    if isinstance(key, str) and key.lower() == 'kubeletidentity'), None)
    kubelet_id = kubelet.object_id if kubelet else None
    version = properties.current_kubernetes_version or properties.kubernetes_version
    workload_identity = security.workload_identity if security else None
    node_mode = properties.node_provisioning_profile.mode if properties.node_provisioning_profile else None
    sku_name = sku.name if sku else None
    requirements = [
        ('AKS mode', sku_name == 'Base' and node_mode != 'Auto',
         f'{sku_name}/{node_mode}', 'Standard AKS offering, not Automatic; no pricing-tier restriction'),
        ('Kubernetes version', _version_at_least(version, '1.31'), version, '>= 1.31'),
        ('AKS identity', bool(identity and identity.type in ('SystemAssigned', 'UserAssigned')),
         identity.type if identity else None, 'Managed identity'),
        ('Kubelet identity', bool(kubelet_id and str(kubelet_id).strip()), kubelet_id,
         'Readable kubelet identity objectId'),
        ('OIDC', bool(oidc and oidc.enabled is True and oidc.issuer_url), oidc.issuer_url if oidc else None,
         'Enabled with readable issuer URL'),
        ('Workload Identity', bool(workload_identity and workload_identity.enabled is True),
         workload_identity.enabled if workload_identity else None, 'Enabled'),
        ('CNI plugin', bool(network and network.network_plugin == 'azure'),
         network.network_plugin if network else None, 'Azure CNI'),
        ('AKS region', bool(cluster.location and cluster.location.lower() == location.lower()),
         cluster.location, location),
    ]
    for name, passed, observed, expected in requirements:
        _report(checks, name, scope, passed, observed, expected, 'Configure a supported AKS cluster and retry.')
    _check_network_policy(network, scope, checks)


def _check_network_policy(network, scope, checks):
    policy = network.network_policy if network else None
    dataplane = network.network_dataplane if network else None
    if dataplane == 'cilium' or policy in ('azure', 'calico'):
        status = 'PASS'
    elif policy == 'none' and dataplane in (None, 'azure'):
        status = 'FAIL'
    else:
        status = 'UNVERIFIED'
    remediation = 'None' if status == 'PASS' else (
        'Enable an AKS-supported network policy engine before retrying. '
        'Missing or custom configurations cannot be verified from AKS resource properties. '
        'This command does not modify the cluster.')
    _report(checks, 'Network policy', scope, status, f'networkPolicy={policy}; networkDataplane={dataplane}',
            'AKS-managed network policy enabled: Azure NPM, Calico or the Cilium dataplane',
            remediation)


def _evaluate_pool(pool):
    properties = pool.properties
    if properties is None:
        return False, False, f'{pool.name}: missing properties'
    requirements = {
        'User': properties.mode == 'User', 'AzureLinux': properties.os_sku in ('AzureLinux', 'AzureLinux3'),
        'KataVmIsolation': properties.workload_runtime == 'KataVmIsolation',
        'count>=1': (properties.count or 0) >= 1,
        'image': _image_supported(properties.node_image_version),
        'label': (properties.node_labels or {}).get('agents.ai.azure.com/sandbox-node') == 'true',
    }
    missing = [key for key, passed in requirements.items() if not passed]
    detail = f'{pool.name}: mode={properties.mode}; missing={missing}'
    return properties.mode == 'System', not missing, detail


def _check_pools(aks, cluster, scope, checks):
    parts = parse_resource_id(scope)
    pools = list(aks.agent_pools.list(parts['resource_group'], parts['name']))
    has_system, has_agent, details = False, False, []
    for pool in pools:
        is_system, is_agent, detail = _evaluate_pool(pool)
        has_system = has_system or is_system
        has_agent = has_agent or is_agent
        details.append(detail)
    _report(checks, 'System node pool', scope, has_system, details, 'At least one System node pool',
            'Prepare a System node pool.')
    _report(checks, 'Agent node pool', scope, has_agent, details,
            'One User pool satisfying all sandbox requirements', 'Prepare one qualifying User pool.')
    network = cluster.properties.network_profile if cluster.properties else None
    mode = network.network_plugin_mode if network else None
    pod_subnets = {pool.name: pool.properties.pod_subnet_id if pool.properties else None for pool in pools}
    uses_pod_subnets = bool(pools) and all(bool(subnet and str(subnet).strip()) for subnet in pod_subnets.values())
    _report(checks, 'CNI mode', scope, mode == 'overlay' or (mode is None and uses_pod_subnets),
            f'{mode}; pool pod subnets={pod_subnets}', 'Azure CNI Overlay or Pod Subnet on every node pool',
            'Use Azure CNI Overlay or configure a Pod subnet on every node pool.')


def _storage_parameters(location, tags, sku):
    return {
        'location': location, 'kind': 'StorageV2', 'tags': tags,
        'sku': {'name': sku},
        'properties': {
            'accessTier': 'Hot', 'isHnsEnabled': False, 'publicNetworkAccess': 'Enabled',
            'networkAcls': {'defaultAction': 'Allow'}, 'minimumTlsVersion': 'TLS1_2',
            'supportsHttpsTrafficOnly': True, 'allowBlobPublicAccess': False, 'allowSharedKeyAccess': False,
        },
    }


def _check_storage(storage, scope, location, checks):
    properties = storage.properties
    if properties is None:
        _report(checks, 'Storage readiness', scope, 'UNVERIFIED', 'Missing properties', 'Succeeded',
                'Read a fully provisioned Storage account.')
        return
    requirements = [
        ('Storage region', _normalize_location(storage.location) == _normalize_location(location),
         storage.location, location),
        ('Storage readiness', properties.provisioning_state == 'Succeeded', properties.provisioning_state, 'Succeeded'),
        ('Storage kind', storage.kind == 'StorageV2', storage.kind, 'StorageV2'),
        ('Storage tier', properties.access_tier == 'Hot', properties.access_tier, 'Hot'),
        ('Storage HNS', properties.is_hns_enabled is not True, properties.is_hns_enabled,
         'Disabled (false or omitted)'),
        ('Storage HTTPS', properties.enable_https_traffic_only is True, properties.enable_https_traffic_only, True),
        ('Storage TLS', properties.minimum_tls_version in ('TLS1_2', 'TLS1_3'),
         properties.minimum_tls_version, '>=TLS1_2'),
    ]
    for name, passed, observed, expected in requirements:
        _report(checks, name, scope, passed, observed, expected, 'Supply Storage with the required configuration.')
    sku = str(_enum_value(storage.sku.name)) if storage.sku and storage.sku.name else ''
    zone_redundant = sku.endswith(('ZRS', 'GZRS'))
    _report(checks, 'Storage redundancy', scope, 'PASS' if sku else 'UNVERIFIED',
            sku or 'Missing SKU', 'Readable redundancy; ZRS or GZRS recommended',
            'None' if zone_redundant else 'Use ZRS or GZRS when available.', mandatory=False)


def _role_guid(role_definition_id):
    return role_definition_id.rstrip('/').rsplit('/', 1)[-1].lower() if role_definition_id else ''


def _accepted_role_ids(role_name):
    role_id = _ROLE_IDS[role_name]
    if role_name == 'Storage Blob Data Contributor':
        return {role_id, _ROLE_IDS['Storage Blob Data Owner']}
    return {role_id, _ROLE_IDS['Owner'], _ROLE_IDS['Contributor']}


def _assigned_role_ids(client, scope, principal, cache):
    key = scope.lower()
    if key not in cache:
        cache[key] = list(client.role_assignments.list_for_scope(scope, filter='atScope()'))
    principal = principal.lower()
    return {
        _role_guid(assignment.properties.role_definition_id)
        for assignment in cache[key]
        if (assignment.properties and assignment.properties.principal_id and
            assignment.properties.principal_id.lower() == principal and not assignment.properties.condition and
            assignment.properties.role_definition_id)
    }


def _check_grants(cli_ctx, clients, request, checked, checks):
    resources = checked.resources
    assignments_by_scope = {}
    grants = [
        (resources.management_identity, checked.management_identity, resources.cluster,
         'Reader', request.management_identity is not None),
        (resources.management_identity, checked.management_identity, resources.cluster,
         'Kubernetes Extension Contributor', request.management_identity is not None),
        (resources.management_identity, checked.management_identity, resources.workload_identity,
         'Managed Identity Federated Identity Credential Contributor',
         request.management_identity is not None and request.workload_identity is not None),
        (resources.workload_identity, checked.workload_identity, resources.storage,
         'Storage Blob Data Contributor',
         request.workload_identity is not None and request.storage is not None),
    ]
    assignments = []
    for identity_id, identity, scope, role_name, validation in grants:
        if validation:
            client = _clients(cli_ctx, scope, clients).authorization
            principal = identity.principal_id if identity else None
            assigned = _assigned_role_ids(client, scope, principal, assignments_by_scope) if principal else set()
            allowed = bool(assigned & _accepted_role_ids(role_name))
            _report(checks, f'{role_name} validation', scope, allowed, f'{principal}: {role_name}',
                    'Existing effective role assignment; no grant writes',
                    'Have an administrator grant the required role assignment.')
        else:
            role_id = (f'/subscriptions/{parse_resource_id(scope)["subscription"]}'
                       f'/providers/Microsoft.Authorization/roleDefinitions/{_ROLE_IDS[role_name]}')
            assignments.append(Grant(role_name, identity_id, scope, role_id))
    return assignments
