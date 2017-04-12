# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import tempfile
import unittest
import uuid
import mock

from azure.mgmt.authorization.models import RoleDefinition, RoleDefinitionProperties
from azure.graphrbac.models import Application, ServicePrincipal
from azure.cli.command_modules.role.custom import (create_role_definition,
                                                   update_role_definition,
                                                   create_service_principal_for_rbac)

# pylint: disable=line-too-long


class TestRoleMocked(unittest.TestCase):

    def setUp(self):
        self.role_logical_name = 'test-role'
        self.subscription_id = 'sub123'
        self.default_scope = '/subscriptions/' + self.subscription_id
        self.sample_role_def = {
            'Name': self.role_logical_name,
            'Description': 'Can monitor compute, network and storage, and restart virtual machines',
            'Actions': [
                'Microsoft.Compute/virtualMachines/start/action',
                'Microsoft.Compute/virtualMachines/restart/action',
                'Microsoft.Network/*/read',
                'Microsoft.Storage/*/read',
                'Microsoft.Authorization/*/read'
            ],
            'AssignableScopes': [self.default_scope]
        }
        self.create_def_invoked = False
        self.update_def_invoked = False

    @mock.patch('azure.cli.command_modules.role.custom._auth_client_factory', autospec=True)
    def test_create_role_definition(self, client_mock):

        def _create_def(role_definition_id, scope, role_definition):
            self.create_def_invoked = True
            uuid.UUID(str(role_definition_id))  # as long as no exception, it means a generated uuid
            self.assertEqual(self.default_scope, scope)
            self.assertEqual(role_definition.properties.role_name, self.role_logical_name)

        faked_role_client = mock.MagicMock()
        client_mock.return_value = faked_role_client
        faked_role_client.role_definitions.create_or_update = _create_def

        _, role_definition_file = tempfile.mkstemp()
        with open(role_definition_file, 'w') as f:
            json.dump(self.sample_role_def, f)
        role_definition_file = role_definition_file.replace('\\', '\\\\')

        # action
        create_role_definition(role_definition_file)

        # assert
        self.assertTrue(self.create_def_invoked)

    @mock.patch('azure.cli.command_modules.role.custom._auth_client_factory', autospec=True)
    def test_update_role_definition(self, client_mock):
        test_role_id = '2ac90824-b711-4809-bec9-4c85809d1111'

        def _update_def(role_definition_id, scope, role_definition):
            self.update_def_invoked = True
            self.assertEqual(role_definition_id, test_role_id)
            self.assertEqual(self.default_scope, scope)
            self.assertEqual(role_definition.properties.role_name, self.role_logical_name)

        faked_role_client = mock.MagicMock()
        client_mock.return_value = faked_role_client
        faked_role_client.role_definitions.create_or_update = _update_def
        faked_role_client.config.subscription_id = self.subscription_id
        faked_role_client.role_definitions.list.return_value = [RoleDefinition(name=test_role_id,
                                                                               properties=RoleDefinitionProperties(role_name=self.role_logical_name))]

        _, role_definition_file = tempfile.mkstemp()
        with open(role_definition_file, 'w') as f:
            json.dump(self.sample_role_def, f)
        role_definition_file = role_definition_file.replace('\\', '\\\\')

        # action
        update_role_definition(role_definition_file)

        # assert
        self.assertTrue(self.update_def_invoked)

    @mock.patch('azure.cli.command_modules.role.custom._auth_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    def test_create_for_rbac_password_plumbed_through(self, graph_client_mock, auth_client_mock):
        faked_role_client = mock.MagicMock()
        auth_client_mock.return_value = faked_role_client
        faked_role_client.config.subscription_id = self.subscription_id

        faked_graph_client = mock.MagicMock()
        graph_client_mock.return_value = faked_graph_client

        test_pwd = 'verySecret'
        name = 'mysp'
        test_app_id = 'app_id_123'
        app = Application(app_id=test_app_id)
        faked_graph_client.applications.create.return_value = app
        sp = ServicePrincipal(object_id='does not matter')
        faked_graph_client.service_principals.create.return_value = sp

        # action
        result = create_service_principal_for_rbac(name, test_pwd, 12, skip_assignment=True)

        # assert
        self.assertEqual(result['password'], test_pwd)
        self.assertEqual(result['name'], 'http://' + name)
        self.assertEqual(result['appId'], test_app_id)


class FakedResponse(object):  # pylint: disable=too-few-public-methods
    def __init__(self, status_code):
        self.status_code = status_code


if __name__ == '__main__':
    unittest.main()
