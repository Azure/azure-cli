# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import unittest
from dataclasses import replace
from itertools import product
from types import SimpleNamespace
from unittest import mock

from azure.core.exceptions import HttpResponseError, ResourceExistsError, ResourceNotFoundError
from azure.mgmt.authorization.models import Permission, RoleAssignment, RoleDefinition
from azure.mgmt.compute.models import ResourceSku
from azure.mgmt.containerservice.models import AgentPool, ManagedCluster
from azure.mgmt.cognitiveservices.models import Account
from azure.mgmt.storage.models import SkuInformation, StorageAccount
from azure.cli.core.azclierror import InvalidArgumentValueError, ValidationError
from azure.cli.command_modules.cognitiveservices._agent_hosting import (
    prepare_agent_hosting, provision, _ensure_grant,
)
from azure.cli.command_modules.cognitiveservices._agent_hosting_preflight import (
    Grant, build_request, preflight, _has_permissions, _image_supported,
    _names, _operator_requirements, _permission_allows,
    _resolve_resources, _select_storage_sku, _storage_parameters, validate_resource_ids,
)


_SUB = '00000000-0000-0000-0000-000000000000'
_RG = f'/subscriptions/{_SUB}/resourceGroups/rg'
_CLUSTER = _RG + '/providers/Microsoft.ContainerService/managedClusters/cluster'
_STORAGE = _RG + '/providers/Microsoft.Storage/storageAccounts/storage'
_MANAGEMENT = _RG + '/providers/Microsoft.ManagedIdentity/userAssignedIdentities/management'
_WORKLOAD = _RG + '/providers/Microsoft.ManagedIdentity/userAssignedIdentities/workload'
_VNET = _RG + '/providers/Microsoft.Network/virtualNetworks/vnet'
_NODE_SUBNET = _VNET + '/subnets/nodes'
_AGENT_SUBNET = _VNET + '/subnets/agents'
_PREFIX = 'azure.cli.command_modules.cognitiveservices._agent_hosting.'
_PREFLIGHT_PREFIX = 'azure.cli.command_modules.cognitiveservices._agent_hosting_preflight.'


class AgentHostingPreparationTests(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = mock.Mock()
        self.tags = {'user-tag': 'value'}
        patcher = mock.patch('azure.cli.core.commands.client_factory.get_subscription_id', return_value=_SUB)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('azure.cli.core._profile.Profile')
        profile = patcher.start()
        self.profile = profile.return_value
        self.addCleanup(patcher.stop)
        self.cognitive = mock.Mock()
        self.cognitive.accounts.get.side_effect = ResourceNotFoundError('Account not found')
        self.cognitive.check_domain_availability.return_value = SimpleNamespace(is_subdomain_available=True, reason=None)
        patcher = mock.patch(_PREFLIGHT_PREFIX + 'get_cognitiveservices_management_client', return_value=self.cognitive)
        self.cognitive_factory = patcher.start()
        self.addCleanup(patcher.stop)
        self.cluster = {
            'location': 'westus', 'sku': {'name': 'Base', 'tier': 'Standard'},
            'identity': {'type': 'SystemAssigned'}, 'properties': {
                'provisioningState': 'Succeeded', 'kubernetesVersion': '1.31.0',
                'oidcIssuerProfile': {'enabled': True, 'issuerURL': 'https://issuer.example/'},
                'securityProfile': {'workloadIdentity': {'enabled': True}},
                'networkProfile': {
                    'networkPlugin': 'azure', 'networkPluginMode': 'overlay', 'networkDataplane': 'cilium'},
            },
        }
        self.pools = [
            {'name': 'system', 'properties': {
                'mode': 'System', 'vmSize': 'Standard_D4s_v5', 'provisioningState': 'Succeeded'}},
            {'name': 'agents', 'properties': {
                'mode': 'User', 'vmSize': 'Standard_D8s_v5', 'count': 1, 'osSKU': 'AzureLinux',
                'workloadRuntime': 'KataVmIsolation', 'nodeImageVersion': 'AKSAzureLinux-V3katagen2-202608.14.0',
                'nodeLabels': {'agents.ai.azure.com/sandbox-node': 'true'},
                'securityProfile': {'sshAccess': 'Disabled'}, 'provisioningState': 'Succeeded',
                'vnetSubnetID': _NODE_SUBNET,
            }},
        ]
        self.storage = {
            'id': _STORAGE, 'location': 'westus', 'kind': 'StorageV2',
            'sku': {'name': 'Standard_ZRS'}, 'properties': {
                'provisioningState': 'Succeeded', 'accessTier': 'Hot', 'isHnsEnabled': False,
                'supportsHttpsTrafficOnly': True, 'minimumTlsVersion': 'TLS1_2',
                'allowSharedKeyAccess': False, 'allowBlobPublicAccess': False,
                'publicNetworkAccess': 'Enabled', 'networkAcls': {'defaultAction': 'Allow'},
                'primaryEndpoints': {'blob': 'https://storage.blob.core.windows.net/'},
            },
        }
        self.roles = {}
        role_permissions = {
            'Owner': {'actions': ['*']},
            'Reader': {'actions': ['*/read']},
            'Kubernetes Extension Contributor': {
                'actions': ['Microsoft.KubernetesConfiguration/extensions/*']},
            'Managed Identity Federated Identity Credential Contributor': {
                'actions': ['Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials/*']},
            'Storage Blob Data Contributor': {
                'actions': ['Microsoft.Storage/storageAccounts/blobServices/containers/*'],
                'dataActions': ['Microsoft.Storage/storageAccounts/blobServices/containers/blobs/*']},
        }
        for index, (name, permission) in enumerate(role_permissions.items()):
            self.roles[name] = {
                'id': f'/subscriptions/{_SUB}/providers/Microsoft.Authorization/roleDefinitions/role{index}',
                'roleName': name, 'roleType': 'BuiltInRole', 'permissions': [permission]}
        self.assignments = [self._assignment('operator', 'Owner', f'/subscriptions/{_SUB}')]
        self.clients = {name: mock.Mock() for name in (
            'aks', 'compute', 'storage', 'identity', 'resource', 'authorization', 'subscription')}
        self.clients['subscription'].subscriptions.get.return_value = SimpleNamespace(tenant_id='tenant')
        self.clients['resource'].resource_groups.check_existence.return_value = True
        self.clients['aks'].managed_clusters.get.side_effect = lambda *args: ManagedCluster(self.cluster)
        self.clients['aks'].agent_pools.list.side_effect = lambda *args: [AgentPool(pool) for pool in self.pools]
        self.clients['compute'].resource_skus.list.return_value = [
            ResourceSku.deserialize({'name': name, 'resourceType': 'virtualMachines', 'capabilities': [
                {'name': 'vCPUs', 'value': str(cores)}, {'name': 'MemoryGB', 'value': str(memory)}]})
            for name, cores, memory in (('Standard_D4s_v5', 4, 16), ('Standard_D8s_v5', 8, 32))]
        self.clients['identity'].user_assigned_identities.get.side_effect = self._get_identity
        self.clients['identity'].user_assigned_identities.create_or_update.side_effect = self._create_identity
        self.clients['storage'].storage_accounts.get_properties.side_effect = self._get_storage
        self.clients['storage'].storage_accounts.check_name_availability.return_value = SimpleNamespace(
            name_available=True, message=None)
        self.clients['storage'].skus.list.return_value = [
            SimpleNamespace(name='Standard_ZRS', kind='StorageV2', locations=['westus'], restrictions=[])]
        self.clients['storage'].storage_accounts.begin_create.return_value.result.side_effect = (
            lambda: StorageAccount(self.storage))
        auth = self.clients['authorization']
        auth.role_definitions.list.side_effect = lambda scope, filter: [self._sdk_role(self.roles[filter.split("'")[1]])]
        auth.role_definitions.get_by_id.side_effect = lambda arm_id: self._sdk_role(next(
            role for role in self.roles.values() if role['id'] == arm_id))
        auth.role_assignments.list_for_scope.side_effect = lambda scope, **kwargs: [
            RoleAssignment({'id': item['id'], 'properties': item})
            for item in self.assignments if scope.lower() == item['scope'].lower() or
            scope.lower().startswith(item['scope'].lower() + '/')]
        auth.role_assignments.create.side_effect = lambda scope, name, parameters: RoleAssignment({
            'id': f'{scope}/providers/Microsoft.Authorization/roleAssignments/{name}'})
        self._configure_caller_permissions(auth, _SUB)
        patcher = mock.patch(_PREFIX + 'get_agent_hosting_clients', side_effect=self._subscription_clients)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(_PREFLIGHT_PREFIX + 'get_agent_hosting_clients', side_effect=self._subscription_clients)
        self.client_factory = patcher.start()
        self.addCleanup(patcher.stop)

    def _caller_permissions(self, scope):
        for assignment in self.assignments:
            if assignment['principalId'] not in ('operator', 'operator-group'):
                continue
            if not (scope.lower() == assignment['scope'].lower() or
                    scope.lower().startswith(assignment['scope'].lower() + '/')):
                continue
            role = next(role for role in self.roles.values() if role['id'] == assignment['roleDefinitionId'])
            for permission in role['permissions']:
                properties = dict(permission)
                if assignment.get('condition'):
                    properties['condition'] = assignment['condition']
                yield Permission(properties)

    def _configure_caller_permissions(self, client, subscription):
        client.permissions.list_for_resource_group.side_effect = (
            lambda group: self._caller_permissions(f'/subscriptions/{subscription}/resourceGroups/{group}'))
        client.permissions.list_for_resource.side_effect = (
            lambda group, namespace, parent, resource_type, name: self._caller_permissions(
                f'/subscriptions/{subscription}/resourceGroups/{group}/providers/{namespace}/{resource_type}/{name}'))

    def _subscription_clients(self, cli_ctx, subscription):
        clients = dict(self.clients)
        if subscription != _SUB:
            authorization = mock.Mock()
            authorization.role_assignments = clients['authorization'].role_assignments
            authorization.role_definitions = clients['authorization'].role_definitions
            self._configure_caller_permissions(authorization, subscription)
            clients['authorization'] = authorization
        return SimpleNamespace(**clients)

    @staticmethod
    def _sdk_role(role):
        return RoleDefinition({'id': role['id'], 'properties': {
            'roleName': role['roleName'], 'type': role['roleType'], 'permissions': role['permissions']}})

    def _assignment(self, principal, role, scope, **kwargs):
        return {'id': scope + '/providers/Microsoft.Authorization/roleAssignments/' + principal + role,
                'principalId': principal, 'scope': scope, 'roleDefinitionId': self.roles[role]['id'], **kwargs}

    def _get_identity(self, group, name):
        if name in ('management', 'workload'):
            return SimpleNamespace(principal_id=name + '-principal', id=_MANAGEMENT if name == 'management'
                                   else _WORKLOAD, client_id='client-id', tenant_id='tenant-id')
        raise ResourceNotFoundError('Not found')

    @staticmethod
    def _create_identity(group, name, parameters):
        return SimpleNamespace(id=_RG + '/providers/Microsoft.ManagedIdentity/userAssignedIdentities/' + name,
                               principal_id=name + '-principal', client_id='client-id', tenant_id='tenant-id')

    def _get_storage(self, group, name):
        if name == 'storage':
            return StorageAccount(self.storage)
        raise ResourceNotFoundError('Not found')

    def _prepare(self, management=True, workload=True, storage=True, subnet=None):
        preparation = build_request(
            SimpleNamespace(cli_ctx=self.cli_ctx), 'rg', 'foundry', 'westus',
            cluster=_CLUSTER, management_identity=_MANAGEMENT if management else None,
            workload_identity=_WORKLOAD if workload else None, storage=_STORAGE if storage else None, subnet=subnet)
        assignments = [
            self._assignment('management-principal', 'Reader', _CLUSTER),
            self._assignment('management-principal', 'Kubernetes Extension Contributor', _CLUSTER),
            self._assignment('management-principal', 'Managed Identity Federated Identity Credential Contributor',
                             _WORKLOAD),
            self._assignment('workload-principal', 'Storage Blob Data Contributor', _STORAGE),
        ]
        existing = {assignment['id'] for assignment in self.assignments}
        self.assignments.extend(assignment for assignment in assignments if assignment['id'] not in existing)
        return preparation

    def _assert_no_writes(self):
        self.clients['resource'].resource_groups.create_or_update.assert_not_called()
        self.clients['identity'].user_assigned_identities.create_or_update.assert_not_called()
        self.clients['storage'].storage_accounts.begin_create.assert_not_called()
        self.clients['authorization'].role_assignments.create.assert_not_called()

    def test_account_name_validation_precedes_dependency_queries(self):
        for name in ('a', 'a' * 65, 'bad.name', '-bad'):
            with self.subTest(name=name):
                with self.assertRaisesRegex(InvalidArgumentValueError, '--name'):
                    prepare_agent_hosting(SimpleNamespace(cli_ctx=self.cli_ctx), 'rg', name, 'westus',
                                          self.tags, cluster=_CLUSTER)
                self._assert_no_writes()
        self.client_factory.assert_not_called()
        self.cognitive_factory.assert_not_called()

    def test_new_account_checks_actual_custom_domain_with_root_client(self):
        preflight(self.cli_ctx, self._prepare(), kind='AIServices', custom_domain='actual-domain')
        self.cognitive.accounts.get.assert_called_once_with('rg', 'foundry')
        self.cognitive.check_domain_availability.assert_called_once()
        parameters = self.cognitive.check_domain_availability.call_args.args[0]
        self.assertEqual(parameters.subdomain_name, 'actual-domain')
        self.assertEqual(parameters.type, 'Microsoft.CognitiveServices/accounts')
        self.assertEqual(parameters.kind, 'AIServices')
        self._assert_no_writes()

    def test_existing_account_checks_new_or_previously_absent_custom_domain(self):
        self.cognitive.accounts.get.side_effect = None
        for previous in ('old-domain', None):
            with self.subTest(previous=previous):
                self.cognitive.check_domain_availability.reset_mock()
                self.cognitive.accounts.get.return_value = Account({'properties': {'customSubDomainName': previous}})
                preflight(self.cli_ctx, self._prepare(), kind='AIServices', custom_domain='new-domain')
                self.assertEqual(
                    self.cognitive.check_domain_availability.call_args.args[0].subdomain_name, 'new-domain')
                self._assert_no_writes()

    def test_unavailable_or_unverified_domain_blocks_dependency_creation(self):
        for available in (False, None):
            with self.subTest(available=available):
                self.cognitive.check_domain_availability.return_value = SimpleNamespace(
                    is_subdomain_available=available, reason='Domain is already in use')
                with self.assertRaisesRegex(ValidationError, 'not available'):
                    preflight(self.cli_ctx, self._prepare(), kind='AIServices', custom_domain='taken-domain')
                self._assert_no_writes()
        self.clients['identity'].user_assigned_identities.get.assert_not_called()

    def test_account_read_errors_are_not_treated_as_not_found(self):
        error = HttpResponseError('Account read failed')
        error.status_code = 403
        self.cognitive.accounts.get.side_effect = error
        with self.assertRaises(HttpResponseError) as caught:
            preflight(self.cli_ctx, self._prepare(), kind='AIServices', custom_domain='new-domain')
        self.assertIs(caught.exception, error)
        self.cognitive.check_domain_availability.assert_not_called()
        self._assert_no_writes()

    def test_domain_api_error_is_preserved(self):
        error = HttpResponseError('Domain check forbidden')
        self.cognitive.check_domain_availability.side_effect = error
        with self.assertRaises(HttpResponseError) as caught:
            preflight(self.cli_ctx, self._prepare(), kind='AIServices', custom_domain='new-domain')
        self.assertIs(caught.exception, error)
        self._assert_no_writes()

    def test_command_validates_ids_once_and_passes_kind_and_domain(self):
        from azure.cli.command_modules.cognitiveservices.custom import create
        self._prepare(False, False, False)
        client = mock.Mock()
        with mock.patch(_PREFLIGHT_PREFIX + 'validate_resource_ids', wraps=validate_resource_ids) as validate:
            result = create(SimpleNamespace(cli_ctx=self.cli_ctx), client, 'rg', 'foundry', 'S0', 'AIServices', 'westus',
                            custom_domain='actual-domain', agent_hosting_cluster=_CLUSTER, subnet=_AGENT_SUBNET)
        validate.assert_called_once()
        self.assertIs(result, client.begin_create.return_value)
        self.assertEqual(self.cognitive.check_domain_availability.call_args.args[0].kind, 'AIServices')
        payload = client.begin_create.call_args.args[2].as_dict()
        self.assertEqual(payload['properties']['customSubDomainName'], 'actual-domain')
        self.assertEqual(payload['properties']['networkInjections'][0]['subnetArmId'], _AGENT_SUBNET)
        self.clients['resource'].resource_groups.create_or_update.assert_not_called()
        self.clients['resource'].resources.get_by_id.assert_not_called()

    def test_all_eight_dependency_and_grant_branches(self):
        for management, workload, storage in product((False, True), repeat=3):
            with self.subTest(management=management, workload=workload, storage=storage):
                for client in self.clients.values():
                    client.reset_mock()
                preparation = self._prepare(management, workload, storage)
                checked = preflight(self.cli_ctx, preparation)
                resolved = provision(self.cli_ctx, checked, self.tags)
                self.assertEqual(self.clients['identity'].user_assigned_identities.create_or_update.call_count,
                                 int(not management) + int(not workload))
                self.assertEqual(self.clients['storage'].storage_accounts.begin_create.call_count, int(not storage))
                expected_grants = 2 * int(not management) + int(not (management and workload)) + int(
                    not (workload and storage))
                self.assertEqual(self.clients['authorization'].role_assignments.create.call_count, expected_grants)
                self.assertEqual(resolved['storage'], _STORAGE if storage else _resolve_resources(preparation).storage)
                if not storage:
                    parameters = self.clients['storage'].storage_accounts.begin_create.call_args.args[2]
                    self.assertEqual(parameters['tags'], self.tags)

    def test_supplied_dependencies_need_no_grant_write_permission(self):
        self.roles['Owner']['permissions'][0]['notActions'] = ['Microsoft.Authorization/roleAssignments/write']
        preparation = self._prepare()
        checked = preflight(self.cli_ctx, preparation)
        provision(self.cli_ctx, checked, self.tags)
        self._assert_no_writes()

    def test_operator_requirements_follow_request_intent_and_target_scope(self):
        request = self._prepare(False, False, False)
        checked = SimpleNamespace(
            resources=_resolve_resources(request), management_identity=None, workload_identity=None, storage=None)
        required = _operator_requirements(request, checked)
        self.assertEqual(required.count(
            (_RG, 'Microsoft.ManagedIdentity/userAssignedIdentities/write')), 1)

        other = '11111111-1111-1111-1111-111111111111'
        management = _MANAGEMENT.replace(_SUB, other).replace('/resourceGroups/rg/', '/resourceGroups/identity-rg/')
        request = replace(self._prepare(), management_identity=management)
        checked = SimpleNamespace(
            resources=_resolve_resources(request), management_identity=None, workload_identity=object(), storage=object())
        required = _operator_requirements(request, checked)
        self.assertNotIn((_RG, 'Microsoft.ManagedIdentity/userAssignedIdentities/write'), required)
        self.assertNotIn((_RG, 'Microsoft.Storage/storageAccounts/write'), required)
        self.assertIn((
            f'/subscriptions/{other}/resourceGroups/identity-rg',
            'Microsoft.ManagedIdentity/userAssignedIdentities/assign/action'), required)

    def test_account_cluster_and_storage_require_same_subscription(self):
        request = self._prepare()
        other = '11111111-1111-1111-1111-111111111111'
        for field in ('cluster', 'storage'):
            with self.subTest(field=field):
                supplied = replace(request, **{field: getattr(request, field).replace(_SUB, other)})
                with self.assertRaisesRegex(InvalidArgumentValueError, 'same subscription'):
                    preflight(self.cli_ctx, supplied)
                self._assert_no_writes()
        self.client_factory.assert_not_called()

    def test_cross_subscription_workload_identity_is_allowed_in_same_tenant(self):
        request = self._prepare(management=False)
        other = '11111111-1111-1111-1111-111111111111'
        supplied = replace(request, workload_identity=_WORKLOAD.replace(_SUB, other))
        self.assignments.append(self._assignment('operator', 'Owner', f'/subscriptions/{other}'))
        checked = preflight(self.cli_ctx, supplied)
        result = provision(self.cli_ctx, checked, self.tags)
        self.assertEqual(result['workload_identity'], supplied.workload_identity)
        self.assertTrue(any(call.args[1] == other for call in self.client_factory.call_args_list))
        self.clients['authorization'].role_assignments.create.assert_any_call(
            supplied.workload_identity, mock.ANY, mock.ANY)

    def test_existing_workload_identity_requires_all_three_metadata_fields(self):
        original = self.clients['identity'].user_assigned_identities.get.side_effect
        for field in ('principal_id', 'client_id', 'tenant_id'):
            with self.subTest(field=field):
                def get_identity(group, name, field=field):
                    identity = original(group, name)
                    if name == 'workload':
                        setattr(identity, field, None)
                    return identity
                self.clients['identity'].user_assigned_identities.get.side_effect = get_identity
                with self.assertRaises(ValidationError):
                    preflight(self.cli_ctx, self._prepare())
                self._assert_no_writes()

    def test_created_workload_identity_requires_all_three_metadata_fields(self):
        original = self.clients['identity'].user_assigned_identities.create_or_update.side_effect
        request = self._prepare(False, False, False)
        checked = preflight(self.cli_ctx, request)
        for field in ('principal_id', 'client_id', 'tenant_id'):
            with self.subTest(field=field):
                def create_identity(group, name, parameters, field=field):
                    identity = original(group, name, parameters)
                    if name.endswith('-workload-mi'):
                        setattr(identity, field, None)
                    return identity
                self.clients['identity'].user_assigned_identities.create_or_update.side_effect = create_identity
                with self.assertRaisesRegex(ValidationError, 'missing metadata'):
                    provision(self.cli_ctx, checked, self.tags)
                self.clients['storage'].storage_accounts.begin_create.assert_not_called()

    def test_workload_identity_does_not_require_operator_assign_action(self):
        self.roles['Owner']['permissions'][0]['notActions'] = [
            'Microsoft.ManagedIdentity/userAssignedIdentities/assign/action']
        self.roles['Identity Assigner'] = {
            'id': f'/subscriptions/{_SUB}/providers/Microsoft.Authorization/roleDefinitions/assigner',
            'roleName': 'Identity Assigner', 'roleType': 'CustomRole',
            'permissions': [{'actions': ['Microsoft.ManagedIdentity/userAssignedIdentities/assign/action']}],
        }
        self.assignments.append(self._assignment('operator', 'Identity Assigner', _MANAGEMENT))
        preflight(self.cli_ctx, self._prepare())
        self._assert_no_writes()

    def test_standard_aks_offering_does_not_restrict_pricing_tier(self):
        self.cluster['sku']['tier'] = 'Free'
        preflight(self.cli_ctx, self._prepare())
        self._assert_no_writes()

    def test_automatic_cluster_is_rejected(self):
        self.cluster['sku']['name'] = 'Automatic'
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, self._prepare())
        self._assert_no_writes()

    def test_system_pool_must_be_succeeded(self):
        self.pools[0]['properties']['provisioningState'] = 'Updating'
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, self._prepare())
        self._assert_no_writes()

    def test_sandbox_label_requires_exact_lowercase_true(self):
        for value in ('True', None):
            with self.subTest(value=value):
                self.pools[1]['properties']['nodeLabels']['agents.ai.azure.com/sandbox-node'] = value
                with self.assertRaises(ValidationError):
                    preflight(self.cli_ctx, self._prepare())
                self._assert_no_writes()

    def test_missing_validation_permission_blocks_without_repair(self):
        preparation = self._prepare()
        self.assignments = [assignment for assignment in self.assignments
                            if assignment['principalId'] != 'workload-principal']
        with self.assertRaisesRegex(ValidationError, 'No Azure resources were written'):
            preflight(self.cli_ctx, preparation)
        self._assert_no_writes()

    def test_partial_custom_grants_must_cover_all_existing_requirements(self):
        request = self._prepare()
        self.assignments = [assignment for assignment in self.assignments
                            if assignment['principalId'] != 'management-principal' or
                            assignment['scope'] != _CLUSTER]
        self.roles['Limited Hosting'] = {
            'id': f'/subscriptions/{_SUB}/providers/Microsoft.Authorization/roleDefinitions/limited',
            'roleName': 'Limited Hosting', 'roleType': 'CustomRole',
            'permissions': [{'actions': ['*'], 'notActions': ['*/write']}],
        }
        self.assignments.append(self._assignment('management-principal', 'Limited Hosting', _CLUSTER))
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, request)
        self._assert_no_writes()

        self.roles['Extension Writer'] = {
            'id': f'/subscriptions/{_SUB}/providers/Microsoft.Authorization/roleDefinitions/writer',
            'roleName': 'Extension Writer', 'roleType': 'CustomRole',
            'permissions': [{'actions': ['*/write']}],
        }
        self.assignments.append(self._assignment('management-principal', 'Extension Writer', _CLUSTER))
        checked = preflight(self.cli_ctx, request)
        self.assertTrue(all(check['status'] == 'PASS' for check in checked.checks if check['name'] == 'G01 Validation'))
        self._assert_no_writes()

    def test_blob_validation_does_not_infer_data_access_from_owner(self):
        preparation = self._prepare()
        self.assignments = [assignment for assignment in self.assignments
                            if assignment['principalId'] != 'workload-principal']
        self.assignments.append(self._assignment('workload-principal', 'Owner', _STORAGE))
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, preparation)
        self._assert_no_writes()

    def test_missing_operator_authority_blocks_all_writes(self):
        preparation = self._prepare(management=False)
        self.roles['Owner']['permissions'][0]['notActions'] = ['Microsoft.Authorization/roleAssignments/write']
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, preparation)
        self._assert_no_writes()

    def test_qualifying_requirements_cannot_be_combined_across_pools(self):
        preparation = self._prepare()
        other = copy.deepcopy(self.pools[1])
        other['name'] = 'other'
        other['properties']['nodeLabels'] = {}
        self.pools[1]['properties']['securityProfile']['sshAccess'] = 'LocalUser'
        self.pools.append(other)
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, preparation)
        self._assert_no_writes()

    def test_agent_pool_requirements_each_block_when_missing(self):
        original = copy.deepcopy(self.pools[1])
        for key, value in (
                ('osSKU', 'Ubuntu'), ('count', 0), ('vmSize', 'Standard_D4s_v5'),
                ('workloadRuntime', 'OCIContainer'), ('nodeImageVersion', 'AKSAzureLinux-V3katagen2-202608.13.9'),
                ('nodeLabels', {}), ('securityProfile', {'sshAccess': 'LocalUser'}), ('provisioningState', 'Updating')):
            with self.subTest(key=key):
                self.pools[1] = copy.deepcopy(original)
                self.pools[1]['properties'][key] = value
                with self.assertRaises(ValidationError):
                    preflight(self.cli_ctx, self._prepare())
                self._assert_no_writes()

    def test_autoscaling_does_not_replace_required_existing_agent_node(self):
        self.pools[1]['properties'].update(count=0, enableAutoScaling=True, minCount=0, maxCount=3)
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, self._prepare())
        self._assert_no_writes()

    def test_documented_managed_network_policy_configurations_are_accepted(self):
        for policy, dataplane in (('azure', 'azure'), ('calico', 'azure'), ('azure', None), ('calico', None),
                                  ('cilium', 'cilium'), (None, 'cilium'), ('none', 'cilium')):
            with self.subTest(policy=policy, dataplane=dataplane):
                self.cluster['properties']['networkProfile'].update(
                    networkPolicy=policy, networkDataplane=dataplane)
                checked = preflight(self.cli_ctx, self._prepare())
                statuses = {check['name']: check['status'] for check in checked.checks}
                self.assertEqual(statuses['Network policy'], 'PASS')
                self.assertEqual(statuses['CNI mode'], 'PASS')
                self._assert_no_writes()

    def test_disabled_network_policy_fails_before_writes_even_with_overlay(self):
        self.cluster['properties']['networkProfile'].update(networkPolicy='none', networkDataplane='azure')
        self.cluster['properties']['addonProfiles'] = {'azurepolicy': {'enabled': True}}
        with self.assertLogs('cli.' + _PREFLIGHT_PREFIX.rstrip('.'), level='WARNING') as logs:
            with self.assertRaises(ValidationError):
                preflight(self.cli_ctx, self._prepare())
        self.assertTrue(any('FAIL Network policy' in line for line in logs.output))
        self.assertFalse(any('PASS ' in line for line in logs.output))
        self.clients['aks'].managed_clusters.get.assert_called_once()
        self._assert_no_writes()

    def test_missing_or_unrecognized_network_policy_evidence_blocks_preflight(self):
        for policy, dataplane in ((None, None), (None, 'azure'), ('custom', 'azure'), ('cilium', 'azure'),
                                  (None, 'custom')):
            with self.subTest(policy=policy, dataplane=dataplane):
                self.cluster['properties']['networkProfile'].update(
                    networkPolicy=policy, networkDataplane=dataplane)
                with self.assertLogs('cli.' + _PREFLIGHT_PREFIX.rstrip('.'), level='WARNING') as logs:
                    with self.assertRaises(ValidationError):
                        preflight(self.cli_ctx, self._prepare())
                self.assertTrue(any('UNVERIFIED Network policy' in line for line in logs.output))
                self._assert_no_writes()

    def test_network_policy_is_required_for_pod_subnet_networking(self):
        self.cluster['properties']['networkProfile'].update(
            networkPluginMode=None, networkPolicy='none', networkDataplane='azure')
        for pool in self.pools:
            pool['properties']['podSubnetID'] = _VNET + '/subnets/pods'
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, self._prepare())
        self._assert_no_writes()

    def test_pod_subnet_networking_uses_child_pool_evidence(self):
        self.cluster['properties']['networkProfile']['networkPluginMode'] = None
        for pool in self.pools:
            pool['properties']['podSubnetID'] = _VNET + '/subnets/pods'
        preflight(self.cli_ctx, self._prepare())

    def test_pod_subnet_missing_on_any_pool_is_rejected(self):
        self.cluster['properties']['networkProfile']['networkPluginMode'] = None
        for missing in range(len(self.pools)):
            with self.subTest(pool=self.pools[missing]['name']):
                for index, pool in enumerate(self.pools):
                    pool['properties']['podSubnetID'] = None if index == missing else _VNET + '/subnets/pods'
                with self.assertRaises(ValidationError):
                    preflight(self.cli_ctx, self._prepare())
                self._assert_no_writes()

    def test_kubenet_is_rejected_even_with_overlay_or_pod_subnets(self):
        self.cluster['properties']['networkProfile']['networkPlugin'] = 'kubenet'
        for mode in ('overlay', None):
            with self.subTest(mode=mode):
                self.cluster['properties']['networkProfile']['networkPluginMode'] = mode
                for pool in self.pools:
                    pool['properties']['podSubnetID'] = _VNET + '/subnets/pods'
                with self.assertRaises(ValidationError):
                    preflight(self.cli_ctx, self._prepare())
                self._assert_no_writes()

    def test_explicit_azure_linux_3_os_sku_is_accepted(self):
        self.pools[1]['properties']['osSKU'] = 'AzureLinux3'
        preflight(self.cli_ctx, self._prepare())

    def test_node_subnet_only_networking_is_rejected(self):
        self.cluster['properties']['networkProfile']['networkPluginMode'] = None
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, self._prepare())
        self._assert_no_writes()

    def test_cluster_requirement_failures(self):
        for key, value in (('kubernetesVersion', '1.30.9'), ('provisioningState', 'Updating'),
                           ('oidcIssuerProfile', {}), ('securityProfile', {})):
            with self.subTest(key=key):
                preparation = self._prepare()
                original = self.cluster['properties'][key]
                self.cluster['properties'][key] = value
                with self.assertRaises(ValidationError):
                    preflight(self.cli_ctx, preparation)
                self.cluster['properties'][key] = original
                self._assert_no_writes()

    def test_restricted_storage_warns_without_blocking(self):
        self.storage['properties']['publicNetworkAccess'] = 'Disabled'
        self.storage['sku']['name'] = 'Standard_LRS'
        preparation = self._prepare()
        checked = preflight(self.cli_ctx, preparation)
        checks = {check['name']: check['status'] for check in checked.checks}
        self.assertEqual(checks['Storage public-network baseline'], 'NOT_APPLICABLE')
        self.assertEqual(checks['Storage redundancy'], 'UNVERIFIED')

    def test_invalid_storage_configuration_blocks(self):
        for key, value in (('isHnsEnabled', True), ('allowSharedKeyAccess', True),
                           ('allowBlobPublicAccess', True), ('supportsHttpsTrafficOnly', False),
                           ('minimumTlsVersion', 'TLS1_0'), ('primaryEndpoints', {'blob': 'http://invalid'})):
            with self.subTest(key=key):
                original = self.storage['properties'][key]
                self.storage['properties'][key] = value
                with self.assertRaises(ValidationError):
                    preflight(self.cli_ctx, self._prepare())
                self.storage['properties'][key] = original
                self._assert_no_writes()

    def test_supplied_storage_must_match_account_region(self):
        self.storage['location'] = 'eastus'
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, self._prepare())
        self._assert_no_writes()

    def test_unavailable_generated_storage_name_blocks_before_writes(self):
        self.clients['storage'].storage_accounts.check_name_availability.return_value = SimpleNamespace(
            name_available=False, message='Already taken')
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, self._prepare(storage=False))
        self._assert_no_writes()

    def test_unknown_storage_public_network_state_blocks(self):
        self.storage['properties']['publicNetworkAccess'] = None
        self.storage['properties']['networkAcls'] = None
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, self._prepare())
        self._assert_no_writes()

    def test_resolved_management_and_workload_identity_cannot_be_same(self):
        preparation = self._prepare(workload=False)
        preparation = replace(preparation, management_identity=_resolve_resources(preparation).workload_identity)
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, preparation)
        self._assert_no_writes()

    def test_managed_overlay_does_not_require_node_subnet_or_vnet_permission(self):
        self.pools[1]['properties']['vnetSubnetID'] = None
        self.roles['Owner']['permissions'][0]['notActions'] = ['Microsoft.Network/*']
        for subnet in (None, _AGENT_SUBNET, _AGENT_SUBNET.replace(_SUB, '11111111-1111-1111-1111-111111111111')):
            with self.subTest(subnet=subnet):
                checked = preflight(self.cli_ctx, self._prepare(subnet=subnet))
                self.assertEqual(checked.resources.subnet, subnet)
                self.clients['resource'].resources.get_by_id.assert_not_called()
                self.assertTrue(all(call.args[0] == _SUB
                                    for call in self.clients['subscription'].subscriptions.get.call_args_list))
                self.assertFalse(any('Microsoft.Network/' in str(check['expected']) for check in checked.checks))
                self._assert_no_writes()
        self._assert_no_writes()

    def test_unreadable_resources_are_unverified_not_absent(self):
        self.clients['identity'].user_assigned_identities.get.side_effect = HttpResponseError('Forbidden')
        preparation = self._prepare()
        with self.assertLogs('cli.' + _PREFLIGHT_PREFIX.rstrip('.'), level='WARNING') as logs:
            with self.assertRaises(ValidationError):
                preflight(self.cli_ctx, preparation)
        self.assertTrue(any('UNVERIFIED' in line for line in logs.output))
        self._assert_no_writes()

    def test_preflight_returns_results_without_mutating_request(self):
        request = self._prepare(False, False, False)
        original = copy.deepcopy(request)
        checked = preflight(self.cli_ctx, request)
        self.assertEqual(request, original)
        self.assertIsNone(request.management_identity)
        self.assertIsNotNone(checked.resources.management_identity)
        self.assertEqual(len(checked.grants), 4)
        self.assertIsNone(checked.management_identity)
        self.assertTrue(all(isinstance(grant, Grant) for grant in checked.grants))
        self._assert_no_writes()

    def test_entry_point_does_not_provision_after_failed_preflight(self):
        with mock.patch(_PREFIX + 'build_request', return_value=self._prepare()), \
                mock.patch(_PREFIX + 'preflight', side_effect=ValidationError('Preflight failed')), \
                mock.patch(_PREFIX + 'provision') as create:
            with self.assertRaisesRegex(ValidationError, 'Preflight failed'):
                prepare_agent_hosting(SimpleNamespace(cli_ctx=self.cli_ctx), 'rg', 'foundry',
                                      'westus', self.tags, cluster=_CLUSTER)
        create.assert_not_called()
        self._assert_no_writes()

    def test_cross_tenant_reference_blocks(self):
        preparation = self._prepare()
        preparation = replace(preparation, workload_identity=_WORKLOAD.replace(
            _SUB, '11111111-1111-1111-1111-111111111111'))
        self.clients['subscription'].subscriptions.get.side_effect = lambda subscription: SimpleNamespace(
            tenant_id='tenant' if subscription == _SUB else 'other')
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, preparation)
        self._assert_no_writes()

    def test_unreadable_caller_permissions_block_preflight(self):
        self.clients['authorization'].permissions.list_for_resource_group.side_effect = HttpResponseError('Forbidden')
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, self._prepare())
        self._assert_no_writes()
        self.profile.get_raw_token.assert_not_called()

    def test_unreadable_assignment_authority_is_not_silently_skipped(self):
        self.clients['authorization'].permissions.list_for_resource.side_effect = HttpResponseError('Forbidden')
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, self._prepare(management=False))
        self._assert_no_writes()
        self.profile.get_raw_token.assert_not_called()

    def test_conditional_grants_are_not_unconditional_evidence(self):
        preparation = self._prepare()
        self.assignments[0]['condition'] = 'unverified condition'
        with self.assertRaises(ValidationError):
            preflight(self.cli_ctx, preparation)
        self._assert_no_writes()

    def test_auto_storage_configuration(self):
        for sku in ('Standard_LRS', 'Standard_ZRS'):
            parameters = _storage_parameters('westus', {'user-tag': 'value'}, sku)
            self.assertEqual(parameters['sku']['name'], sku)
            self.assertEqual(parameters['kind'], 'StorageV2')
            self.assertEqual(parameters['tags']['user-tag'], 'value')
            self.assertEqual(parameters['properties'], {
                'accessTier': 'Hot', 'isHnsEnabled': False, 'publicNetworkAccess': 'Enabled',
                'networkAcls': {'defaultAction': 'Allow'}, 'minimumTlsVersion': 'TLS1_2',
                'supportsHttpsTrafficOnly': True, 'allowBlobPublicAccess': False, 'allowSharedKeyAccess': False})

    def test_auto_storage_prefers_zrs_and_falls_back_to_lrs(self):
        zrs = SkuInformation({
            'name': 'Standard_ZRS', 'kind': 'StorageV2', 'locations': ['westus'], 'restrictions': []})
        self.clients['storage'].skus.list.return_value = [zrs]
        self.assertEqual(_select_storage_sku(self.clients['storage'], 'West US'), 'Standard_ZRS')
        zrs = SkuInformation({
            'name': 'Standard_ZRS', 'kind': 'StorageV2', 'locations': ['westus'],
            'restrictions': [{'type': 'location', 'values': ['westus'],
                              'reasonCode': 'NotAvailableForSubscription'}]})
        self.clients['storage'].skus.list.return_value = [zrs]
        self.assertEqual(_select_storage_sku(self.clients['storage'], 'westus'), 'Standard_LRS')
        zrs = SkuInformation({
            'name': 'Standard_ZRS', 'kind': 'StorageV2', 'locations': ['eastus'], 'restrictions': []})
        self.clients['storage'].skus.list.return_value = [zrs]
        self.assertEqual(_select_storage_sku(self.clients['storage'], 'westus'), 'Standard_LRS')

    def test_missing_group_blocks_before_any_dependency_write(self):
        self.clients['resource'].resource_groups.check_existence.return_value = False
        with self.assertRaisesRegex(ValidationError, 'does not exist'):
            preflight(self.cli_ctx, self._prepare(False, False, False))
        self._assert_no_writes()
        self.clients['aks'].managed_clusters.get.assert_not_called()

    def test_group_read_error_is_preserved(self):
        error = HttpResponseError('Forbidden')
        error.status_code = 403
        self.clients['resource'].resource_groups.check_existence.side_effect = error
        with self.assertRaises(HttpResponseError) as caught:
            preflight(self.cli_ctx, self._prepare())
        self.assertIs(caught.exception, error)
        self._assert_no_writes()

    def test_existing_generated_dependencies_are_reused_without_updates(self):
        preparation = self._prepare(False, False, False)
        self.clients['identity'].user_assigned_identities.get.side_effect = (
            lambda group, name: self._create_identity(group, name, None))
        self.clients['storage'].storage_accounts.get_properties.side_effect = lambda *args: StorageAccount(self.storage)
        checked = preflight(self.cli_ctx, preparation)
        provision(self.cli_ctx, checked, self.tags)
        self.clients['identity'].user_assigned_identities.create_or_update.assert_not_called()
        self.clients['storage'].storage_accounts.begin_create.assert_not_called()

    def test_assignment_names_are_stable_across_retries(self):
        preparation = self._prepare(False, False, False)
        checked = preflight(self.cli_ctx, preparation)
        provision(self.cli_ctx, checked, self.tags)
        first = [call.args[1] for call in self.clients['authorization'].role_assignments.create.call_args_list]
        self.clients['authorization'].role_assignments.create.reset_mock()
        preparation = self._prepare(False, False, False)
        checked = preflight(self.cli_ctx, preparation)
        provision(self.cli_ctx, checked, self.tags)
        second = [call.args[1] for call in self.clients['authorization'].role_assignments.create.call_args_list]
        self.assertEqual(first, second)

    def test_compatible_existing_grant_is_not_recreated(self):
        self._prepare()
        role = self._sdk_role(self.roles['Reader'])
        _ensure_grant(self.clients['authorization'], Grant('G01', _MANAGEMENT, _CLUSTER, role.id),
                      'management-principal')
        self.clients['authorization'].role_assignments.create.assert_not_called()

    @staticmethod
    def _conflict(code='RoleAssignmentExists', status=409):
        error = ResourceExistsError('Role assignment conflict')
        error.status_code = status
        error.error = SimpleNamespace(code=code)
        return error

    def test_role_assignment_race_reuses_only_verified_identical_assignment(self):
        self._prepare()
        grant = Grant('G01', _MANAGEMENT, _CLUSTER, self.roles['Reader']['id'])
        assignment = RoleAssignment({
            'id': _CLUSTER + '/providers/Microsoft.Authorization/roleAssignments/existing',
            'properties': {'principalId': 'MANAGEMENT-PRINCIPAL',
                           'roleDefinitionId': grant.role_id.upper(), 'scope': _CLUSTER.upper()},
        })
        client = self.clients['authorization']
        client.role_assignments.list_for_scope.side_effect = [[], [assignment]]
        client.role_assignments.create.side_effect = self._conflict()
        _ensure_grant(client, grant, 'management-principal')
        self.assertEqual(client.role_assignments.list_for_scope.call_count, 2)
        client.role_assignments.create.assert_called_once()

    def test_role_assignment_conflict_must_match_principal_role_scope_and_condition(self):
        grant = Grant('G01', _MANAGEMENT, _CLUSTER, self.roles['Reader']['id'])
        base = {'principalId': 'management-principal', 'roleDefinitionId': grant.role_id, 'scope': _CLUSTER}
        cases = [
            {'principalId': 'another-principal'}, {'roleDefinitionId': 'another-role'}, {'scope': _RG},
            {'scope': None}, {'condition': 'unverified condition'},
        ]
        client = self.clients['authorization']
        for changed in cases:
            with self.subTest(changed=changed):
                assignment = RoleAssignment({'properties': {**base, **changed}})
                error = self._conflict()
                client.role_assignments.list_for_scope.side_effect = [[], [assignment]]
                client.role_assignments.create.side_effect = error
                with self.assertRaises(ResourceExistsError) as caught:
                    _ensure_grant(client, grant, 'management-principal')
                self.assertIs(caught.exception, error)

    def test_unverified_role_assignment_conflict_preserves_original_error(self):
        client = self.clients['authorization']
        grant = Grant('G01', _MANAGEMENT, _CLUSTER, self.roles['Reader']['id'])
        for second_read in ([], HttpResponseError('Read forbidden')):
            with self.subTest(second_read=second_read):
                error = self._conflict()
                client.role_assignments.list_for_scope.side_effect = [[], second_read]
                client.role_assignments.create.side_effect = error
                with self.assertRaises(ResourceExistsError) as caught:
                    _ensure_grant(client, grant, 'management-principal')
                self.assertIs(caught.exception, error)

    def test_other_role_assignment_errors_are_not_ignored(self):
        client = self.clients['authorization']
        grant = Grant('G01', _MANAGEMENT, _CLUSTER, self.roles['Reader']['id'])
        for code, status in (('RoleAssignmentUpdateNotPermitted', 409), ('RoleAssignmentExists', 403)):
            with self.subTest(code=code, status=status):
                client.reset_mock()
                error = self._conflict(code, status)
                client.role_assignments.list_for_scope.side_effect = [[]]
                client.role_assignments.create.side_effect = error
                with self.assertRaises(ResourceExistsError) as caught:
                    _ensure_grant(client, grant, 'management-principal')
                self.assertIs(caught.exception, error)
                client.role_assignments.list_for_scope.assert_called_once()

    def test_service_errors_are_preserved_with_visible_resource_context(self):
        preparation = self._prepare(False, False, False)
        error = HttpResponseError('Service failure with correlation ID')
        self.clients['storage'].storage_accounts.begin_create.side_effect = error
        with self.assertLogs('cli.' + _PREFIX.rstrip('.'), level='WARNING') as logs:
            with self.assertRaises(HttpResponseError) as caught:
                prepare_agent_hosting(SimpleNamespace(cli_ctx=self.cli_ctx), 'rg', 'foundry', 'westus', self.tags,
                                      cluster=_CLUSTER)
        self.assertIs(caught.exception, error)
        for arm_id in (_resolve_resources(preparation).management_identity,
                       _resolve_resources(preparation).workload_identity, _resolve_resources(preparation).storage):
            self.assertTrue(any(arm_id in line for line in logs.output))
        self.assertTrue(any('not automatically deleted' in line for line in logs.output))
        self.assertEqual(self.clients['identity'].user_assigned_identities.create_or_update.call_count, 2)

class AgentHostingValueTests(unittest.TestCase):
    def test_resource_type_validation(self):
        for key in ('cluster', 'storage', 'management_identity', 'workload_identity', 'subnet'):
            with self.subTest(key=key):
                with self.assertRaises(InvalidArgumentValueError):
                    validate_resource_ids(**{
                        'cluster': _CLUSTER, key: _RG + '/providers/Microsoft.Compute/virtualMachines/vm'})
        with self.assertRaises(InvalidArgumentValueError):
            validate_resource_ids(cluster=_CLUSTER, management_identity=_MANAGEMENT, workload_identity=_MANAGEMENT)

    def test_deterministic_account_based_names(self):
        names = _names(_SUB, 'rg', 'team-ai-prod')
        self.assertTrue(names['storage'].startswith('teamaiprod'))
        self.assertLessEqual(len(names['storage']), 24)
        self.assertEqual(names['management_identity'], 'team-ai-prod-hosting-mi')
        self.assertEqual(names, _names(_SUB.upper(), 'RG', 'TEAM-AI-PROD'))
        self.assertNotEqual(names['storage'], _names(_SUB, 'other-rg', 'team-ai-prod')['storage'])

    def test_image_baseline_accepts_only_same_series_at_or_above_minimum(self):
        for image in ('AKSAzureLinux-V3katagen2-202608.14.0', 'AKSAzureLinux-V3katagen2-202609.1.0'):
            self.assertTrue(_image_supported(image))
        for image in (None, '', 'AKSAzureLinux-V3katagen2-202608.13.9', 'AKSUbuntu-202610.1.0',
                      'AKSAzureLinux-V3katagen2-invalid'):
            self.assertFalse(_image_supported(image))

    def test_wildcard_requirements_do_not_bypass_write_or_delete_exclusions(self):
        action = 'Microsoft.KubernetesConfiguration/extensions/*'
        for operation in ('read', 'write', 'delete'):
            with self.subTest(operation=operation):
                permission = Permission({'actions': ['*'], 'notActions': [f'*/{operation}']})
                self.assertFalse(_permission_allows(permission, action))

    def test_another_role_can_fill_only_the_missing_wildcard_actions(self):
        requirement = 'Microsoft.KubernetesConfiguration/extensions/*'
        incomplete = Permission({'actions': ['*'], 'notActions': ['*/write']})
        writer = Permission({'actions': ['*/write']})
        self.assertFalse(_has_permissions([incomplete], [requirement]))
        self.assertTrue(_has_permissions([incomplete, writer], [requirement]))
        self.assertTrue(_has_permissions([writer, incomplete], [requirement]))
        specific_writer = Permission({'actions': ['Microsoft.KubernetesConfiguration/extensions/write']})
        self.assertTrue(_has_permissions([incomplete, specific_writer], [
            'Microsoft.KubernetesConfiguration/extensions/read',
            'Microsoft.KubernetesConfiguration/extensions/write',
        ]))
        self.assertFalse(_has_permissions([incomplete, specific_writer], [requirement]))

    def test_excluded_or_conditional_grants_cannot_take_fast_path(self):
        required = 'Microsoft.Storage/storageAccounts/*'
        for properties in (
                {'actions': ['*'], 'notActions': ['*/write']},
                {'actions': [required], 'notActions': ['*/write']},
                {'actions': ['*'], 'condition': 'unverified'},
                {'actions': [required + 'read']},
                {'dataActions': ['*']}):
            with self.subTest(properties=properties):
                self.assertFalse(_has_permissions([Permission(properties)], [required]))

    def test_wildcard_data_permissions_use_their_own_exclusions_and_grants(self):
        required = 'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/*'
        incomplete = Permission({'dataActions': ['*'], 'notDataActions': ['*/delete']})
        delete = Permission({'dataActions': ['*/delete']})
        self.assertFalse(_has_permissions([incomplete], [required], data=True))
        self.assertTrue(_has_permissions([incomplete, delete], [required], data=True))
        self.assertFalse(_has_permissions([Permission({'actions': ['*']}), delete], [required], data=True))
        management_exclusions = Permission({'dataActions': ['*'], 'notActions': ['*']})
        self.assertTrue(_has_permissions([management_exclusions], [required], data=True))
