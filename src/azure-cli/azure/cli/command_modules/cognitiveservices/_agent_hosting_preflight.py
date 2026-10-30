# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import hashlib
import re
from contextlib import contextmanager
from dataclasses import dataclass, replace
from fnmatch import fnmatchcase
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlparse

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
    'subnet': 'Microsoft.Network/virtualNetworks/subnets',
}


_OPTION_NAMES = {
    'cluster': '--agent-hosting-cluster', 'storage': '--agent-hosting-storage',
    'management_identity': '--agent-hosting-management-identity',
    'workload_identity': '--agent-hosting-workload-identity', 'subnet': '--agent-subnet',
}


@dataclass(frozen=True)
class HostingRequest:
    account_id: str
    location: str
    cluster: str
    storage: Optional[str] = None
    management_identity: Optional[str] = None
    workload_identity: Optional[str] = None
    subnet: Optional[str] = None


@dataclass(frozen=True)
class Grant:
    name: str
    identity_id: str
    scope: str
    role_id: str


@dataclass(frozen=True)
class PreflightResult:
    resources: HostingRequest
    management_identity: Optional['Identity']
    workload_identity: Optional['Identity']
    storage: Optional['StorageAccount']
    storage_sku: Optional[str] = None
    grants: tuple[Grant, ...] = ()
    checks: tuple = ()


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
    _check_account_hosting(existing_account, resources)
    account_clients = _clients(cli_ctx, request.account_id, clients)
    if not account_clients.resource.resource_groups.check_existence(account['resource_group']):
        raise ValidationError(
            f"Resource group '{account['resource_group']}' does not exist. Create it before retrying.")
    _report(checks, 'Resource group', request.account_id, True, 'Exists', 'Existing resource group', 'None')
    if custom_domain:
        _check_domain(cognitive_client, existing_account, custom_domain, kind)
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
            _check_pools(cluster_clients.aks, cluster_clients.compute, cluster,
                         resources.cluster, request.location, checks)
    checked = PreflightResult(resources, management, workload, storage, storage_sku)
    grants = ()
    with _read_check(checks, 'Permissions', request.account_id):
        grants = _check_permissions(cli_ctx, clients, request, checked, checks)
    if any(check['mandatory'] and check['status'] in ('FAIL', 'UNVERIFIED') for check in checks):
        raise ValidationError('BYO AKS preflight failed. No Azure resources were written. '
                              'Resolve the reported FAIL/UNVERIFIED checks and retry.')
    logger.warning('Preflight does not verify live routing, DNS, connectivity, telemetry egress or RBAC propagation.')
    return replace(checked, grants=tuple(grants), checks=tuple(checks))


def _read_account(client, account):
    try:
        return client.accounts.get(account['resource_group'], account['name'])
    except ResourceNotFoundError:
        return None


def _check_account_hosting(existing, resources):
    if existing is None:
        return
    properties = getattr(existing, 'properties', None)
    if properties is None:
        raise ValidationError(
            f'Existing Account {resources.account_id} returned no readable properties. '
            'Inspect the Account before retrying, or use a different Account.')
    configurations = getattr(properties, 'agent_hosting_configurations', None)
    if configurations is None:
        return
    if not isinstance(configurations, (list, tuple)):
        raise ValidationError(
            f'Existing Account {resources.account_id} returned an ambiguous agent hosting configuration. '
            'Inspect the Account before retrying, or use a different Account.')
    if len(configurations) == 0:
        return
    if len(configurations) != 1 or configurations[0] is None:
        raise ValidationError(
            f'Existing Account {resources.account_id} returned an ambiguous agent hosting configuration. '
            'Inspect the Account before retrying, or use a different Account.')

    expected = {
        'name': 'default',
        'hosting_type': 'ManagedCluster',
        'cluster_resource_id': resources.cluster,
        'hosting_management_identity_resource_id': resources.management_identity,
        'workload_identity_resource_id': resources.workload_identity,
        'storage_account_resource_id': resources.storage,
    }
    configuration = configurations[0]
    fields = (
        ('name', 'name', False),
        ('hosting_type', 'hostingType', False),
        ('cluster_resource_id', 'clusterResourceId', True),
        ('hosting_management_identity_resource_id', 'hostingManagementIdentityResourceId', True),
        ('workload_identity_resource_id', 'workloadIdentityResourceId', True),
        ('storage_account_resource_id', 'storageAccountResourceId', True),
    )
    mismatches = []
    for attribute, display_name, arm_id in fields:
        actual = getattr(configuration, attribute, None)
        expected_value = expected[attribute]
        if not isinstance(actual, str) or not actual.strip():
            raise ValidationError(
                f'Existing Account {resources.account_id} has an incomplete agent hosting configuration '
                f'(missing {display_name}). Inspect the Account before retrying, or use a different Account.')
        if arm_id:
            matches = _normalize_arm_id(actual) == _normalize_arm_id(expected_value)
        else:
            matches = actual == expected_value
        if not matches:
            mismatches.append(display_name)
    if mismatches:
        raise ValidationError(
            f'Existing Account {resources.account_id} has an incompatible agent hosting configuration '
            f'({", ".join(mismatches)}). Updating or removing agentHostingConfigurations is not supported. '
            'Use the existing configuration or create a different Account.')


def _normalize_arm_id(value):
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


def _existing_scope(arm_id, exists):
    if exists:
        return arm_id
    parts = parse_resource_id(arm_id)
    return f'/subscriptions/{parts["subscription"]}/resourceGroups/{parts["resource_group"]}'


def _report(checks, name, scope, passed, observed, expected, remediation, mandatory=True):
    status = passed if isinstance(passed, str) else ('PASS' if passed else 'FAIL')
    checks.append({'name': name, 'scope': scope, 'status': status, 'mandatory': mandatory,
                   'observed': observed, 'expected': expected, 'remediation': remediation})
    log = logger.warning if status in ('FAIL', 'UNVERIFIED') else logger.info
    log('%s %s [%s]: observed=%s; expected=%s; remediation=%s',
        status, name, scope, observed, expected, remediation)


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
        _report(checks, 'AKS state', scope, 'UNVERIFIED', 'Missing properties', 'Succeeded',
                'Read a fully provisioned cluster.')
        return
    properties = cluster.properties
    network, oidc, security = properties.network_profile, properties.oidc_issuer_profile, properties.security_profile
    sku, identity = cluster.sku, cluster.identity
    version = properties.current_kubernetes_version or properties.kubernetes_version
    workload_identity = security.workload_identity if security else None
    node_mode = properties.node_provisioning_profile.mode if properties.node_provisioning_profile else None
    sku_name = sku.name if sku else None
    requirements = [
        ('AKS mode', sku_name == 'Base' and node_mode != 'Auto',
         f'{sku_name}/{node_mode}', 'Standard AKS offering, not Automatic; no pricing-tier restriction'),
        ('Kubernetes version', _version_at_least(version, '1.31'), version, '>= 1.31'),
        ('AKS state', properties.provisioning_state == 'Succeeded', properties.provisioning_state, 'Succeeded'),
        ('AKS identity', bool(identity and identity.type in ('SystemAssigned', 'UserAssigned')),
         identity.type if identity else None, 'Managed identity'),
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


def _pool_vm_sizes(properties):
    sizes, seen = [], set()

    def add(value):
        if value is None or not str(value).strip():
            return
        size = str(value).strip()
        key = size.lower()
        if key not in seen:
            seen.add(key)
            sizes.append(size)

    add(properties.vm_size)
    virtual_machines = properties.virtual_machines_profile
    scale = virtual_machines.scale if virtual_machines else None
    for profile in scale.manual or [] if scale else []:
        add(profile.size)
    for node in properties.virtual_machine_nodes_status or []:
        add(node.size)
    return tuple(sizes)


def _pool_capacity_status(sizes, capacity, minimum_cpu, minimum_memory):
    if not sizes:
        return 'UNVERIFIED', ['No VM size evidence']
    status, evidence = 'PASS', []
    for size in sizes:
        key = size.lower()
        if key not in capacity:
            status = 'UNVERIFIED' if status == 'PASS' else status
            evidence.append(f'{size}: SKU not found')
            continue
        available = capacity[key]
        if available is None:
            status = 'UNVERIFIED' if status == 'PASS' else status
            evidence.append(f'{size}: missing vCPU or MemoryGB capability')
            continue
        cpu, memory = available
        if cpu < minimum_cpu or memory < minimum_memory:
            status = 'FAIL'
        evidence.append(f'{size}: {cpu:g} vCPU/{memory:g} GiB')
    return status, evidence


def _vm_size_capacity(compute, location):
    capacity = {}
    for sku in compute.resource_skus.list(filter=f"location eq '{location}'"):
        if sku.resource_type != 'virtualMachines' or not sku.name:
            continue
        key = sku.name.lower()
        capacity.setdefault(key, None)
        capabilities = {value.name.lower(): value.value for value in sku.capabilities or [] if value.name}
        cores = capabilities.get('vcpusavailable') or capabilities.get('vcpus')
        memory = capabilities.get('memorygb')
        try:
            if cores is not None and memory is not None:
                capacity[key] = float(cores), float(memory)
        except (TypeError, ValueError):
            pass
    return capacity


def _evaluate_pool(pool, capacity):
    properties = pool.properties
    if properties is None:
        return None, None, f'{pool.name}: missing properties'
    sizes = _pool_vm_sizes(properties)
    system_capacity, system_evidence = _pool_capacity_status(sizes, capacity, 4, 16)
    agent_capacity, agent_evidence = _pool_capacity_status(sizes, capacity, 8, 32)
    requirements = {
        'User': properties.mode == 'User', 'AzureLinux': properties.os_sku in ('AzureLinux', 'AzureLinux3'),
        'KataVmIsolation': properties.workload_runtime == 'KataVmIsolation',
        'count>=1': (properties.count or 0) >= 1,
        'image': _image_supported(properties.node_image_version),
        'label': (properties.node_labels or {}).get('agents.ai.azure.com/sandbox-node') == 'true',
        'SSH disabled': bool(properties.security_profile and properties.security_profile.ssh_access == 'Disabled'),
        'Succeeded': properties.provisioning_state == 'Succeeded',
    }
    detail = (
        f'{pool.name}: vmSizes={list(sizes)}; '
        f'systemCapacity={system_capacity} {system_evidence}; '
        f'agentCapacity={agent_capacity} {agent_evidence}; '
        f'missing={[key for key, passed in requirements.items() if not passed]}')
    system_status = system_capacity if (
        properties.mode == 'System' and properties.provisioning_state == 'Succeeded') else None
    return system_status, agent_capacity if all(requirements.values()) else None, detail


def _check_pools(aks, compute, cluster, scope, location, checks):
    parts = parse_resource_id(scope)
    pools = list(aks.agent_pools.list(parts['resource_group'], parts['name']))
    capacity = _vm_size_capacity(compute, location)
    system_statuses, agent_statuses, details = [], [], []
    selected = None
    for pool in pools:
        system_status, agent_status, detail = _evaluate_pool(pool, capacity)
        details.append(detail)
        if system_status:
            system_statuses.append(system_status)
        if agent_status:
            agent_statuses.append(agent_status)
            if agent_status == 'PASS' and selected is None:
                selected = pool
    system_status = 'PASS' if 'PASS' in system_statuses else (
        'UNVERIFIED' if 'UNVERIFIED' in system_statuses else 'FAIL')
    agent_status = 'PASS' if 'PASS' in agent_statuses else (
        'UNVERIFIED' if 'UNVERIFIED' in agent_statuses else 'FAIL')
    _report(checks, 'System node pool', scope, system_status, details, 'One Succeeded System pool >=4 vCPU/16 GiB',
            'Prepare a qualifying System pool.')
    _report(checks, 'Agent node pool', scope, agent_status, details,
            'One User pool satisfying all sandbox requirements', 'Prepare one qualifying User pool.')
    network = cluster.properties.network_profile if cluster.properties else None
    mode = network.network_plugin_mode if network else None
    pod_subnets = {pool.name: pool.properties.pod_subnet_id if pool.properties else None for pool in pools}
    uses_pod_subnets = bool(pools) and all(pod_subnets.values())
    _report(checks, 'CNI mode', scope, mode == 'overlay' or uses_pod_subnets,
            f'{mode}; pool pod subnets={pod_subnets}', 'Azure CNI Overlay or Pod Subnet on every node pool',
            'Use Azure CNI Overlay or configure a Pod subnet on every node pool.')
    return selected


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
    endpoint = properties.primary_endpoints.blob if properties.primary_endpoints else ''
    parsed = urlparse(endpoint or '')
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
        ('Storage shared keys', properties.allow_shared_key_access is False,
         properties.allow_shared_key_access, False),
        ('Storage anonymous Blob', properties.allow_blob_public_access is False,
         properties.allow_blob_public_access, False),
        ('Storage Blob endpoint', parsed.scheme == 'https' and bool(parsed.hostname) and
         not parsed.username and not parsed.password and not parsed.query and not parsed.fragment,
         endpoint, 'Valid HTTPS Blob endpoint'),
    ]
    for name, passed, observed, expected in requirements:
        _report(checks, name, scope, passed, observed, expected, 'Supply Storage with the required configuration.')
    sku = storage.sku.name if storage.sku else ''
    _report(checks, 'Storage redundancy', scope, 'PASS' if sku and sku.endswith(('ZRS', 'GZRS')) else 'UNVERIFIED',
            sku, 'Zone redundancy recommended', 'Consider zone-redundant Storage.', mandatory=False)
    public = properties.public_network_access
    action = properties.network_rule_set.default_action if properties.network_rule_set else None
    restricted = public in ('Disabled', 'SecuredByPerimeter') or action == 'Deny'
    status = 'PASS' if public == 'Enabled' and action == 'Allow' else 'NOT_APPLICABLE' if restricted else 'UNVERIFIED'
    _report(checks, 'Storage public-network baseline', scope, status, f'{public}/{action}',
            'Enabled/Allow for public baseline',
            'Private/restricted Storage connectivity is unverified; verify routing and DNS.', mandatory=not restricted)


def _permission_allows(permission, action, data=False):
    if permission.condition:
        return False
    if '*' in action:
        return _wildcard_action_allowed([permission], action, data)
    allowed = permission.data_actions if data else permission.actions
    excluded = permission.not_data_actions if data else permission.not_actions
    action = action.lower()
    return (any(fnmatchcase(action, pattern.lower()) for pattern in allowed or []) and
            not any(fnmatchcase(action, pattern.lower()) for pattern in excluded or []))


def _action_pattern_step(pattern, positions, character=None):
    if character is not None:
        positions = {position if pattern[position] == '*' else position + 1
                     for position in positions if position < len(pattern) and pattern[position] in ('*', character)}
    expanded = set(positions)
    for position in positions:
        while position < len(pattern) and pattern[position] == '*':
            position += 1
            expanded.add(position)
    return frozenset(expanded)


def _wildcard_action_allowed(permissions, action, data):
    """Find whether any operation in the requested wildcard is left without an effective grant."""
    action = action.lower()
    rules = [
        (tuple(pattern.lower() for pattern in (permission.data_actions if data else permission.actions) or []),
         tuple(pattern.lower() for pattern in (permission.not_data_actions if data else permission.not_actions) or []))
        for permission in permissions if not permission.condition
    ]
    if any(not excluded and ('*' in allowed or action in allowed) for allowed, excluded in rules):
        return True
    grant_patterns = [pattern for allowed, excluded in rules for pattern in allowed + excluded]
    patterns = tuple(dict.fromkeys([action] + grant_patterns))
    indexes = {pattern: index for index, pattern in enumerate(patterns)}
    rules = [(tuple(indexes[pattern] for pattern in allowed), tuple(indexes[pattern] for pattern in excluded))
             for allowed, excluded in rules]
    # All other characters have the same matching behavior, represented by the empty symbol.
    alphabet = (set(''.join(patterns)) - {'*'}) | {''}
    start = tuple(_action_pattern_step(pattern, {0}) for pattern in patterns)
    pending, visited = [start], {start}
    while pending:
        state = pending.pop()
        matches = [len(pattern) in positions for pattern, positions in zip(patterns, state)]
        if matches[0] and not any(any(matches[index] for index in allowed) and
                                  not any(matches[index] for index in excluded) for allowed, excluded in rules):
            return False
        for character in alphabet:
            following = tuple(_action_pattern_step(pattern, positions, character)
                              for pattern, positions in zip(patterns, state))
            if following[0] and following not in visited:
                visited.add(following)
                pending.append(following)
    return True


def _permissions(client, scope, principals, definitions):
    principals = {principal.lower() for principal in principals}
    for assignment in client.role_assignments.list_for_scope(scope, filter='atScope()'):
        properties = assignment.properties
        if (not properties or not properties.principal_id or properties.principal_id.lower() not in principals or
                properties.condition):
            continue
        role_id = properties.role_definition_id
        if role_id not in definitions:
            definitions[role_id] = client.role_definitions.get_by_id(role_id)
        role = definitions[role_id]
        if role.properties:
            yield from role.properties.permissions or []


def _has_permissions(permissions, actions, data=False):
    return all(_wildcard_action_allowed(permissions, action, data) if '*' in action else
               any(_permission_allows(permission, action, data) for permission in permissions) for action in actions)


def _validate_grant(permissions, role):
    required = role.properties.permissions if role.properties else None
    if not required or not any(item.actions or item.data_actions for item in required):
        return False
    return all(_has_permissions(permissions, item.actions or []) and
               _has_permissions(permissions, item.data_actions or [], data=True) for item in required)


def _operator_requirements(request, checked):
    resources = checked.resources
    parent = _existing_scope(resources.account_id, False)
    required = [(parent, 'Microsoft.CognitiveServices/accounts/write')]
    if request.management_identity is None or request.workload_identity is None:
        required.append((parent, 'Microsoft.ManagedIdentity/userAssignedIdentities/write'))
    if request.storage is None:
        required.append((parent, 'Microsoft.Storage/storageAccounts/write'))
    identity_scope = _existing_scope(resources.management_identity, checked.management_identity is not None)
    required.append((identity_scope, 'Microsoft.ManagedIdentity/userAssignedIdentities/assign/action'))
    cluster = parse_resource_id(resources.cluster)
    required.append((f'/subscriptions/{cluster["subscription"]}/resourceGroups/{cluster["resource_group"]}',
                     'Microsoft.ContainerService/managedClusters/write'))
    return required


def _operator_permissions(cli_ctx, clients, scope, cache):
    key = scope.lower()
    if key not in cache:
        parts = parse_resource_id(scope)
        client = _clients(cli_ctx, scope, clients).authorization
        if parts.get('namespace'):
            permissions = client.permissions.list_for_resource(
                parts['resource_group'], parts['namespace'], '', parts['type'], parts['name'])
        else:
            permissions = client.permissions.list_for_resource_group(parts['resource_group'])
        cache[key] = list(permissions)
    return cache[key]


def _check_permissions(cli_ctx, clients, request, checked, checks):
    logger.warning('Permission checks verify unconditional RBAC allows only; deny assignments, conditions, '
                   'tenant policy and RBAC propagation are not fully evaluated.')
    required = _operator_requirements(request, checked)
    definitions, operator_permissions = {}, {}
    for scope, action in required:
        permissions = _operator_permissions(cli_ctx, clients, scope, operator_permissions)
        allowed = any(_permission_allows(permission, action) for permission in permissions)
        _report(checks, 'Operator permission', scope, allowed, action if allowed else f'Missing {action}',
                action, 'Have an administrator grant the required unconditional permission.')
    return _check_grants(cli_ctx, clients, request, checked, operator_permissions, definitions, checks)


def _required_role(client, scope, name):
    subscription_scope = f'/subscriptions/{parse_resource_id(scope)["subscription"]}'
    roles = [role for role in client.role_definitions.list(subscription_scope, filter=f"roleName eq '{name}'")
             if role.properties and role.properties.role_name == name and role.properties.role_type == 'BuiltInRole']
    if len(roles) != 1:
        raise ValidationError(f'Cannot resolve the built-in role {name} at {subscription_scope}.')
    return roles[0]


def _check_grants(cli_ctx, clients, request, checked, operator_permissions, definitions, checks):
    resources = checked.resources
    grants = [
        ('G01', resources.management_identity, checked.management_identity, resources.cluster, True,
         'Reader', request.management_identity is not None),
        ('G01', resources.management_identity, checked.management_identity, resources.cluster, True,
         'Kubernetes Extension Contributor', request.management_identity is not None),
        ('G02', resources.management_identity, checked.management_identity, resources.workload_identity,
         checked.workload_identity is not None, 'Managed Identity Federated Identity Credential Contributor',
         request.management_identity is not None and request.workload_identity is not None),
        ('G03', resources.workload_identity, checked.workload_identity, resources.storage,
         checked.storage is not None, 'Storage Blob Data Contributor',
         request.workload_identity is not None and request.storage is not None),
    ]
    assignments = []
    for name, identity_id, identity, scope, exists, role_name, validation in grants:
        client = _clients(cli_ctx, scope, clients).authorization
        role = _required_role(client, scope, role_name)
        if validation:
            principal = identity.principal_id if identity else None
            permissions = list(_permissions(client, scope, [principal], definitions)) if principal else []
            allowed = bool(principal and _validate_grant(permissions, role))
            _report(checks, f'{name} Validation', scope, allowed, f'{principal}: {role_name}',
                    'Existing effective permission; no grant writes',
                    'Have an administrator grant missing permissions.')
        else:
            parent = _existing_scope(scope, exists)
            permissions = _operator_permissions(cli_ctx, clients, parent, operator_permissions)
            allowed = any(_permission_allows(permission, 'Microsoft.Authorization/roleAssignments/write')
                          for permission in permissions)
            _report(checks, f'{name} Assignment authority', parent, allowed, role_name,
                    'Unconditional roleAssignments/write', 'Have an administrator grant role-assignment authority.')
            assignments.append(Grant(name, identity_id, scope, role.id))
    return assignments
