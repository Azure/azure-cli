# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from itertools import combinations
from unittest import mock

from azure.cli.core.azclierror import InvalidArgumentValueError, RequiredArgumentMissingError
from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests.const import MOCKED_SUBSCRIPTION_ID

from azure.cli.command_modules.cognitiveservices.custom import (
    create as account_create,
    update as account_update,
)


class CognitiveServicesAgentHostingUnitTests(unittest.TestCase):
    RESOURCE_GROUP = 'myResourceGroup'
    ACCOUNT_NAME = 'myAccount'
    MANAGEMENT_IDENTITY = (
        f'/subscriptions/{MOCKED_SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/'
        'Microsoft.ManagedIdentity/userAssignedIdentities/account-control-plane'
    )
    WORKLOAD_IDENTITY = (
        f'/subscriptions/{MOCKED_SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/'
        'Microsoft.ManagedIdentity/userAssignedIdentities/aks-workload'
    )
    CLUSTER_ID = (
        f'/subscriptions/{MOCKED_SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/'
        'Microsoft.ContainerService/managedClusters/cluster1'
    )
    STORAGE_ID = (
        f'/subscriptions/{MOCKED_SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/'
        'Microsoft.Storage/storageAccounts/storage1'
    )
    HOSTING_ARGUMENTS = {
        'agent_hosting_cluster': CLUSTER_ID,
        'agent_hosting_storage': STORAGE_ID,
        'agent_hosting_management_identity': MANAGEMENT_IDENTITY,
        'agent_hosting_workload_identity': WORKLOAD_IDENTITY,
    }

    def setUp(self):
        patcher = mock.patch('azure.cli.command_modules.cognitiveservices._agent_hosting.prepare_agent_hosting')
        self.prepare = patcher.start()
        self.addCleanup(patcher.stop)
        self.prepare.return_value = {
            'storage': self.STORAGE_ID, 'management_identity': self.MANAGEMENT_IDENTITY,
            'workload_identity': self.WORKLOAD_IDENTITY,
        }

    def _call_create(self, include_hosting=True, **overrides):
        client = overrides.pop('client', mock.Mock())
        arguments = {
            'cmd': mock.Mock(),
            'client': client,
            'resource_group_name': self.RESOURCE_GROUP,
            'account_name': self.ACCOUNT_NAME,
            'sku_name': 'S0',
            'kind': 'AIServices',
            'location': 'westus',
        }
        if include_hosting:
            arguments.update(self.HOSTING_ARGUMENTS)
        arguments.update(overrides)
        result = account_create(**arguments)
        return client, result

    def _assert_invalid_hosting_arguments(self, arguments, option):
        client = mock.Mock()
        with self.assertRaisesRegex(InvalidArgumentValueError, option):
            self._call_create(client=client, **arguments)
        client.begin_create.assert_not_called()

    def test_agent_hosting_builds_expected_payload(self):
        client, result = self._call_create()

        self.assertIs(result, client.begin_create.return_value)
        client.get.assert_not_called()
        request = client.begin_create.call_args.args[2].as_dict()
        self.assertEqual(
            request['properties']['agentHostingConfigurations'],
            [{
                'name': 'default',
                'hostingManagementIdentityResourceId': self.MANAGEMENT_IDENTITY,
                'workloadIdentityResourceId': self.WORKLOAD_IDENTITY,
                'clusterResourceId': self.CLUSTER_ID,
                'storageAccountResourceId': self.STORAGE_ID,
                'hostingType': 'ManagedCluster',
            }],
        )
        self.assertNotIn('networkInjections', request['properties'])
        self.assertEqual(request['identity']['type'], 'SystemAssigned, UserAssigned')
        self.assertEqual(
            request['identity']['userAssignedIdentities'],
            {self.MANAGEMENT_IDENTITY: {}},
        )
        self.assertNotIn(self.WORKLOAD_IDENTITY, request['identity']['userAssignedIdentities'])

    def test_agent_hosting_uses_user_assigned_identity_without_system_identity(self):
        client, _ = self._call_create(kind='Face', assign_identity=False, allow_project_management=False)

        request = client.begin_create.call_args.args[2].as_dict()
        self.assertEqual(request['identity']['type'], 'UserAssigned')
        self.assertEqual(
            request['identity']['userAssignedIdentities'],
            {self.MANAGEMENT_IDENTITY: {}},
        )

    def test_agent_hosting_requires_cluster_and_accepts_optional_dependencies(self):
        for count in range(1, len(self.HOSTING_ARGUMENTS)):
            for provided in combinations(self.HOSTING_ARGUMENTS, count):
                with self.subTest(provided=provided):
                    client = mock.Mock()
                    arguments = {name: self.HOSTING_ARGUMENTS[name] for name in provided}
                    if 'agent_hosting_cluster' in provided:
                        self._call_create(client=client, include_hosting=False, **arguments)
                        client.begin_create.assert_called_once()
                    else:
                        with self.assertRaisesRegex(RequiredArgumentMissingError, '--agent-hosting-cluster'):
                            self._call_create(client=client, include_hosting=False, **arguments)
                        client.begin_create.assert_not_called()

    def test_agent_hosting_minimal_arguments_prepare_dependencies(self):
        client, _ = self._call_create(include_hosting=False, agent_hosting_cluster=self.CLUSTER_ID)
        self.prepare.assert_called_once()
        self.assertIsNone(self.prepare.call_args.kwargs['storage'])
        self.assertEqual(client.begin_create.call_args.args[2].as_dict()['properties']
                         ['agentHostingConfigurations'][0]['storageAccountResourceId'], self.STORAGE_ID)

    def test_agent_hosting_failed_preflight_does_not_submit_account(self):
        from azure.cli.core.azclierror import ValidationError
        self.prepare.side_effect = ValidationError('Preflight failed')
        client = mock.Mock()
        with self.assertRaisesRegex(ValidationError, 'Preflight failed'):
            self._call_create(client=client)
        client.begin_create.assert_not_called()

    def test_agent_hosting_rejects_empty_and_non_string_arguments(self):
        for argument in self.HOSTING_ARGUMENTS:
            invalid_values = ('', '   ', False, 0, 1, [], {})
            for value in invalid_values:
                with self.subTest(argument=argument, value=value):
                    self._assert_invalid_hosting_arguments(
                        {argument: value}, '--' + argument.replace('_', '-'),
                    )

    def test_agent_hosting_rejects_invalid_resource_ids(self):
        for argument in (
            'agent_hosting_cluster',
            'agent_hosting_management_identity',
            'agent_hosting_storage',
            'agent_hosting_workload_identity',
        ):
            for value in ('not-a-resource-id', 'null'):
                with self.subTest(argument=argument, value=value):
                    self._assert_invalid_hosting_arguments(
                        {argument: value}, '--' + argument.replace('_', '-'),
                    )

    def test_agent_hosting_non_byo_create_preserves_existing_payload(self):
        client, _ = self._call_create(include_hosting=False)

        request = client.begin_create.call_args.args[2].as_dict()
        self.assertNotIn('agentHostingConfigurations', request['properties'])
        self.assertNotIn('networkInjections', request['properties'])
        self.assertEqual(request['identity'], {'type': 'SystemAssigned'})

    def test_agent_hosting_account_update_omits_configuration(self):
        client = mock.Mock()

        account_update(
            client,
            self.RESOURCE_GROUP,
            self.ACCOUNT_NAME,
            sku_name='S0',
        )

        request = client.begin_update.call_args.args[2].as_dict()
        self.assertNotIn('agentHostingConfigurations', request['properties'])
        self.assertNotIn('networkInjections', request['properties'])


class CognitiveServicesAgentHostingScenarioTests(ScenarioTest):
    def setUp(self):
        super().setUp()
        patcher = mock.patch('azure.cli.command_modules.cognitiveservices._agent_hosting.prepare_agent_hosting')
        self.prepare = patcher.start()
        self.addCleanup(patcher.stop)
        self.prepare.return_value = {
            'storage': CognitiveServicesAgentHostingUnitTests.STORAGE_ID,
            'management_identity': CognitiveServicesAgentHostingUnitTests.MANAGEMENT_IDENTITY,
            'workload_identity': CognitiveServicesAgentHostingUnitTests.WORKLOAD_IDENTITY,
        }

    def test_cognitiveservices_agent_hosting_flattened_arguments(self):
        with mock.patch(
            'azure.cli.command_modules.cognitiveservices._client_factory.'
            'get_cognitiveservices_management_client'
        ) as get_management_client:
            accounts_client = mock.Mock()
            accounts_client.begin_create.return_value = None
            get_management_client.return_value.accounts = accounts_client

            self.cmd(
                'az cognitiveservices account create '
                '--name myAccount '
                '--resource-group myResourceGroup '
                '--kind AIServices '
                '--sku S0 '
                '--location westus '
                f'--agent-hosting-cluster {CognitiveServicesAgentHostingUnitTests.CLUSTER_ID} '
                f'--agent-hosting-storage {CognitiveServicesAgentHostingUnitTests.STORAGE_ID} '
                '--agent-hosting-management-identity '
                f'{CognitiveServicesAgentHostingUnitTests.MANAGEMENT_IDENTITY} '
                f'--agent-hosting-workload-identity {CognitiveServicesAgentHostingUnitTests.WORKLOAD_IDENTITY}'
            )

            self.assertEqual(
                self.prepare.call_args.kwargs,
                {
                    'kind': 'AIServices',
                    'custom_domain': None,
                    'cluster': CognitiveServicesAgentHostingUnitTests.CLUSTER_ID,
                    'storage': CognitiveServicesAgentHostingUnitTests.STORAGE_ID,
                    'management_identity': CognitiveServicesAgentHostingUnitTests.MANAGEMENT_IDENTITY,
                    'workload_identity': CognitiveServicesAgentHostingUnitTests.WORKLOAD_IDENTITY,
                },
            )
            accounts_client.begin_create.assert_called_once()

    def test_cognitiveservices_agent_hosting_identity_aliases(self):
        with mock.patch(
            'azure.cli.command_modules.cognitiveservices._client_factory.'
            'get_cognitiveservices_management_client'
        ) as get_management_client:
            accounts_client = mock.Mock()
            accounts_client.begin_create.return_value = None
            get_management_client.return_value.accounts = accounts_client

            self.cmd(
                'az cognitiveservices account create '
                '--name myAccount '
                '--resource-group myResourceGroup '
                '--kind AIServices '
                '--sku S0 '
                '--location westus '
                f'--agent-hosting-cluster {CognitiveServicesAgentHostingUnitTests.CLUSTER_ID} '
                f'--agent-hosting-storage {CognitiveServicesAgentHostingUnitTests.STORAGE_ID} '
                f'--agent-hosting-mi {CognitiveServicesAgentHostingUnitTests.MANAGEMENT_IDENTITY} '
                f'--agent-hosting-wi {CognitiveServicesAgentHostingUnitTests.WORKLOAD_IDENTITY}'
            )

            self.assertEqual(
                self.prepare.call_args.kwargs['management_identity'],
                CognitiveServicesAgentHostingUnitTests.MANAGEMENT_IDENTITY,
            )
            self.assertEqual(
                self.prepare.call_args.kwargs['workload_identity'],
                CognitiveServicesAgentHostingUnitTests.WORKLOAD_IDENTITY,
            )
            accounts_client.begin_create.assert_called_once()
