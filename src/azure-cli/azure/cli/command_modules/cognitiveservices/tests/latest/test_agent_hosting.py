# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import json
import os
import tempfile
import unittest
from unittest import mock

from azure.cli.core.azclierror import InvalidArgumentValueError
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
    SUBNET_ID = (
        f'/subscriptions/{MOCKED_SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/'
        'Microsoft.Network/virtualNetworks/vnet1/subnets/agent-subnet'
    )
    CONFIGURATION = {
        'name': 'default',
        'hostingType': 'ManagedCluster',
        'clusterResourceId': CLUSTER_ID,
        'agentSubnetResourceId': SUBNET_ID,
        'hostingManagementIdentityResourceId': MANAGEMENT_IDENTITY,
        'storageAccountResourceId': STORAGE_ID,
        'workloadIdentityResourceId': WORKLOAD_IDENTITY,
    }

    def _call_create(self, **overrides):
        client = overrides.pop('client', mock.Mock())
        arguments = {
            'client': client,
            'resource_group_name': self.RESOURCE_GROUP,
            'account_name': self.ACCOUNT_NAME,
            'sku_name': 'S0',
            'kind': 'AIServices',
            'location': 'westus',
            'agent_hosting': [copy.deepcopy(self.CONFIGURATION)],
        }
        arguments.update(overrides)
        result = account_create(**arguments)
        return client, result

    def _assert_invalid_configuration(self, configuration, error_type=InvalidArgumentValueError):
        client = mock.Mock()
        with self.assertRaises(error_type):
            self._call_create(client=client, agent_hosting=configuration)
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
        self.assertEqual(
            request['properties']['networkInjections'],
            [{
                'scenario': 'agent',
                'subnetArmId': self.SUBNET_ID,
                'useMicrosoftManagedNetwork': False,
            }],
        )
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

    def test_agent_hosting_omits_network_injection_without_subnet(self):
        configuration = copy.deepcopy(self.CONFIGURATION)
        del configuration['agentSubnetResourceId']

        client, _ = self._call_create(agent_hosting=[configuration])

        request = client.begin_create.call_args.args[2].as_dict()
        self.assertIn('agentHostingConfigurations', request['properties'])
        self.assertNotIn('networkInjections', request['properties'])

    def test_agent_hosting_rejects_invalid_collection_shapes(self):
        invalid_values = (
            {},
            [],
            [self.CONFIGURATION, self.CONFIGURATION],
            [1],
        )
        for value in invalid_values:
            with self.subTest(value=value):
                self._assert_invalid_configuration(value)

    def test_agent_hosting_rejects_missing_and_unknown_fields(self):
        missing = copy.deepcopy(self.CONFIGURATION)
        del missing['name']
        unknown = copy.deepcopy(self.CONFIGURATION)
        unknown['unsupported'] = 'value'

        for configuration in (missing, unknown):
            with self.subTest(configuration=configuration):
                self._assert_invalid_configuration([configuration])

    def test_agent_hosting_rejects_empty_and_non_string_fields(self):
        for field_name in self.CONFIGURATION:
            for value in (None, '', '   ', 1):
                with self.subTest(field_name=field_name, value=value):
                    configuration = copy.deepcopy(self.CONFIGURATION)
                    configuration[field_name] = value
                    self._assert_invalid_configuration([configuration])

    def test_agent_hosting_rejects_unsupported_hosting_type(self):
        configuration = copy.deepcopy(self.CONFIGURATION)
        configuration['hostingType'] = 'Unsupported'
        self._assert_invalid_configuration([configuration])

    def test_agent_hosting_rejects_invalid_resource_ids(self):
        for field_name in (
            'clusterResourceId',
            'agentSubnetResourceId',
            'hostingManagementIdentityResourceId',
            'storageAccountResourceId',
            'workloadIdentityResourceId',
        ):
            with self.subTest(field_name=field_name):
                configuration = copy.deepcopy(self.CONFIGURATION)
                configuration[field_name] = 'not-a-resource-id'
                self._assert_invalid_configuration([configuration])

    def test_agent_hosting_non_byo_create_preserves_existing_payload(self):
        client, _ = self._call_create(
            agent_hosting=None,
        )

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
    def test_cognitiveservices_agent_hosting_null_is_ignored(self):
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
                '--agent-hosting null'
            )

            request = accounts_client.begin_create.call_args.args[2].as_dict()
            self.assertNotIn('agentHostingConfigurations', request['properties'])
            self.assertNotIn('networkInjections', request['properties'])

    def test_cognitiveservices_agent_hosting_from_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as configuration_file:
            json.dump([CognitiveServicesAgentHostingUnitTests.CONFIGURATION], configuration_file)
            configuration_file_path = configuration_file.name

        try:
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
                    f'--agent-hosting "@{configuration_file_path}"'
                )

                request = accounts_client.begin_create.call_args.args[2].as_dict()
                self.assertEqual(
                    request['properties']['agentHostingConfigurations'][0]['hostingType'],
                    'ManagedCluster',
                )
                self.assertEqual(
                    request['properties']['networkInjections'][0]['subnetArmId'],
                    CognitiveServicesAgentHostingUnitTests.SUBNET_ID,
                )
        finally:
            os.remove(configuration_file_path)

    def test_cognitiveservices_agent_hosting_argument_validation(self):
        with mock.patch(
            'azure.cli.command_modules.cognitiveservices._client_factory.'
            'get_cognitiveservices_management_client'
        ) as get_management_client:
            get_management_client.return_value.accounts = mock.Mock()
            with self.assertRaisesRegex(InvalidArgumentValueError, 'exactly one'):
                self.cmd(
                    'az cognitiveservices account create '
                    '--name myAccount '
                    '--resource-group myResourceGroup '
                    '--kind AIServices '
                    '--sku S0 '
                    '--location westus '
                    '--agent-hosting "[]"'
                )
