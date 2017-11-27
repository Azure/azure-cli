# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import os
import tempfile
import unittest
import uuid
import mock

from azure.cli.testsdk import TestCli

from azure.mgmt.authorization.models import RoleDefinition, RoleDefinitionProperties
from azure.graphrbac.models import Application, ServicePrincipal, GraphErrorException
from azure.cli.command_modules.role.custom import (create_role_definition,
                                                   update_role_definition,
                                                   create_service_principal_for_rbac,
                                                   reset_service_principal_credential,
                                                   _try_x509_pem)

from knack.util import CLIError

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
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        create_role_definition(cmd, role_definition_file)

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
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        update_role_definition(cmd, role_definition_file)

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
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        result = create_service_principal_for_rbac(cmd, name, test_pwd, 12, skip_assignment=True)

        # assert
        self.assertEqual(result['password'], test_pwd)
        self.assertEqual(result['name'], 'http://' + name)
        self.assertEqual(result['appId'], test_app_id)

    @mock.patch('azure.cli.command_modules.role.custom._auth_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.role.custom.logger', autospec=True)
    def test_create_for_rbac_use_cert_date(self, logger_mock, graph_client_mock, auth_client_mock):
        import OpenSSL.crypto
        test_app_id = 'app_id_123'
        app = Application(app_id=test_app_id)

        def mock_app_create(parameters):
            end_date = parameters.key_credentials[0].end_date
            # sample check the cert's expiration time
            self.assertEqual(end_date.day, 21)
            self.assertEqual(end_date.month, 4)
            return app

        faked_role_client = mock.MagicMock()
        auth_client_mock.return_value = faked_role_client
        faked_role_client.config.subscription_id = self.subscription_id
        faked_graph_client = mock.MagicMock()
        graph_client_mock.return_value = faked_graph_client

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        cert_file = os.path.join(curr_dir, 'cert.pem').replace('\\', '\\\\')
        with open(cert_file) as f:
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, f.read())

        name = 'mysp'
        faked_graph_client.applications.create.side_effect = mock_app_create
        sp = ServicePrincipal(object_id='does not matter')
        faked_graph_client.service_principals.create.return_value = sp

        # action
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        result = create_service_principal_for_rbac(cmd, name, cert=cert, years=2, skip_assignment=True)

        # assert
        self.assertEqual(result['name'], 'http://' + name)
        self.assertEqual(result['appId'], test_app_id)
        self.assertTrue(logger_mock.warning.called)  # we should warn 'years' will be dropped
        self.assertTrue(faked_graph_client.applications.create.called)

    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    def test_reset_credentials_password(self, graph_client_mock):
        patch_invoked = [False]  # to be used in a nested function below, array type is needed to get scoping work
        test_object_id = 'app_object_id'
        test_pwd = 'verySecret'
        name = 'http://mysp'

        def test_patch(id, param):
            patch_invoked[0] = True
            self.assertEqual(id, test_object_id)
            self.assertEqual(1, len(param.password_credentials))
            self.assertEqual(param.password_credentials[0].value, test_pwd)

        faked_graph_client = mock.MagicMock()
        sp_object = mock.MagicMock()
        sp_object.app_id = 'app_id'
        app_object = mock.MagicMock()
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        app_object.object_id = test_object_id

        graph_client_mock.return_value = faked_graph_client
        faked_graph_client.service_principals.list.return_value = [sp_object]
        faked_graph_client.applications.list.return_value = [app_object]
        faked_graph_client.applications.get.side_effect = [app_object]
        faked_graph_client.applications.patch = test_patch
        faked_graph_client.applications.list_password_credentials.side_effect = [ValueError('should not invoke')]

        # action
        reset_service_principal_credential(cmd, name, test_pwd, append=False)

        # assert
        self.assertTrue(patch_invoked[0])

    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    def test_reset_credentials_certificate_append_option(self, graph_client_mock):
        patch_invoked = [False]  # to be used in a nested function below, array type is needed to get scoping work
        test_object_id = 'app_object_id'
        test_cert = _try_x509_pem('\n'.join(['-----BEGIN CERTIFICATE-----',
                                             'MIICoTCCAYkCAgPoMA0GCSqGSIb3DQEBBQUAMBQxEjAQBgNVBAMMCUNMSS1Mb2dp',
                                             'bjAiGA8yMDE3MTExMzIxMjQyMloYDzIwMTgxMTEzMjEyNDI0WjAUMRIwEAYDVQQD',
                                             'DAlDTEktTG9naW4wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCtyRA6',
                                             'mbUtByQBODMlp3r5fGpnYCfRhAzp2U29KRVTOQK1ntMIo3FWR19ceqK6T0UM+BFb',
                                             'XGn28hGhgz5Y1lrbqyKrAcF10/3y42wmiMyPWjmXJ+WOEKjckKKzPMm2KBsn/ePV',
                                             'qsr5UwlnHh2rGFR0PF1qjC0IU/SI0UQN0KJKpVp0OB8+lRlIAcsLUTveTXbdFDlp',
                                             'k5AA8w3TTo7pT5sKNZr3+qv1o4ogDfDEx0bCYtlm4L1HvGer4pbX7q35ucZY9BWq',
                                             'VjHQ/MjiuAyxZoyY5xVoULMWJupRyMT3wP1Hb+oJ9/tTBZbpNTv1ed9OswCc2W1l',
                                             'MQzLwE10Ev0LJkhlAgMBAAEwDQYJKoZIhvcNAQEFBQADggEBAF+RP+7uzmf4u4+l',
                                             'xjS+lXd3O0tqTNOVe8RR+GXl1s2Un6UhwmP3SKs2RNcXkb9+6Q4Zvg7GODK7Z8th',
                                             't/enpTcvLmPmq2ow1hFGWJk/lONZtVKU2mikTY/ICnQrbhf3WYr1cuf98CRqoG71',
                                             'ldrjgSsM1Ut7Gee1Tpc2eamRtHTm07AUQhqGnS5wVp6s1HUd43nvu/lVx+j2hjEB',
                                             'y63BSuD3aSUweVne4roBNcBJjLU1wvYl+3cLgnZ9///3y/C4pKebsKHljkejRaer',
                                             'nvbPfW9hy7BqMem7t0Qk2D84VzaK+6x9EnnsXy+90nfvTLUSqpU1MjpdWhuWyxDL',
                                             'p4oYS5Q=',
                                             '-----END CERTIFICATE-----']))
        key_id_of_existing_cert = 'existing cert'
        name = 'http://mysp'

        def test_patch(id, param):
            patch_invoked[0] = True
            self.assertEqual(id, test_object_id)
            self.assertEqual(2, len(param.key_credentials))
            self.assertTrue(len(param.key_credentials[1].value) > 0)
            self.assertEqual(param.key_credentials[1].type, 'AsymmetricX509Cert')
            self.assertEqual(param.key_credentials[1].usage, 'Verify')
            self.assertEqual(param.key_credentials[0].key_id, key_id_of_existing_cert)

        faked_graph_client = mock.MagicMock()
        sp_object = mock.MagicMock()
        sp_object.app_id = 'app_id'
        app_object = mock.MagicMock()
        app_object.object_id = test_object_id
        key_cred = mock.MagicMock()
        key_cred.key_id = key_id_of_existing_cert
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()

        graph_client_mock.return_value = faked_graph_client
        faked_graph_client.service_principals.list.return_value = [sp_object]
        faked_graph_client.applications.list.return_value = [app_object]
        faked_graph_client.applications.get.side_effect = [app_object]
        faked_graph_client.applications.patch = test_patch
        faked_graph_client.applications.list_key_credentials.return_value = [key_cred]

        # action
        reset_service_principal_credential(cmd, name, cert=test_cert, append=True)

        # assert
        self.assertTrue(patch_invoked[0])

    @mock.patch('azure.cli.command_modules.role.custom._auth_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    def test_create_for_rbac_failed_with_polished_error_if_due_to_permission(self, graph_client_mock, auth_client_mock):
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        TestRoleMocked._common_rbac_err_polish_test_mock_setup(graph_client_mock, auth_client_mock,
                                                               'Insufficient privileges to complete the operation',
                                                               self.subscription_id)

        # action
        with self.assertRaises(CLIError) as context:
            create_service_principal_for_rbac(cmd, 'will-fail', skip_assignment=True)

        # assert we handled such error
        self.assertTrue('https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal' in str(context.exception))

    @mock.patch('azure.cli.command_modules.role.custom._auth_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    def test_create_for_rbac_failed_with_regular_error(self, graph_client_mock, auth_client_mock):
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        TestRoleMocked._common_rbac_err_polish_test_mock_setup(graph_client_mock, auth_client_mock,
                                                               'something bad for you',
                                                               self.subscription_id)
        # action
        with self.assertRaises(GraphErrorException):
            create_service_principal_for_rbac(cmd, 'will-fail')

    @staticmethod
    def _common_rbac_err_polish_test_mock_setup(graph_client_mock, auth_client_mock, error_msg, subscription_id):
        def _test_deserializer(resp_type, response):
            err = FakedError(error_msg)
            return err

        faked_role_client = mock.MagicMock()
        faked_role_client.config.subscription_id = subscription_id
        auth_client_mock.return_value = faked_role_client
        faked_graph_client = mock.MagicMock()
        graph_client_mock.return_value = faked_graph_client

        faked_graph_client.applications.create.side_effect = GraphErrorException(_test_deserializer, None)


class FakedError(object):  # pylint: disable=too-few-public-methods
    def __init__(self, message):
        self.message = message


if __name__ == '__main__':
    unittest.main()
