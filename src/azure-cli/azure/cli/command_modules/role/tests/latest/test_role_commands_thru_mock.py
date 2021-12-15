# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import os
import tempfile
import unittest
import uuid
from unittest import mock

from azure.cli.core.mock import DummyCli

from azure.mgmt.authorization.models import RoleDefinition, RoleAssignmentCreateParameters
from azure.graphrbac.models import (Application, ServicePrincipal, GraphErrorException,
                                    ApplicationUpdateParameters, GetObjectsParameters)
from azure.cli.command_modules.role.custom import (create_role_definition,
                                                   update_role_definition,
                                                   create_service_principal_for_rbac,
                                                   reset_service_principal_credential,
                                                   update_application, _try_x509_pem,
                                                   delete_service_principal_credential,
                                                   list_service_principal_credentials,
                                                   update_application,
                                                   _get_object_stubs,
                                                   list_service_principal_owners,
                                                   list_application_owners,
                                                   delete_role_assignments)

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
            self.assertEqual(role_definition.role_name, self.role_logical_name)

        faked_role_client = mock.MagicMock()
        client_mock.return_value = faked_role_client
        faked_role_client.role_definitions.create_or_update = _create_def

        _, role_definition_file = tempfile.mkstemp()
        with open(role_definition_file, 'w') as f:
            json.dump(self.sample_role_def, f)
        role_definition_file = role_definition_file.replace('\\', '\\\\')

        # action
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
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
            self.assertEqual(role_definition.role_name, self.role_logical_name)

        faked_role_client = mock.MagicMock()
        client_mock.return_value = faked_role_client
        faked_role_client.role_definitions.create_or_update = _update_def
        faked_role_client.config.subscription_id = self.subscription_id

        test_def = RoleDefinition(role_name=self.role_logical_name)
        test_def.name = test_role_id
        faked_role_client.role_definitions.list.return_value = [test_def]

        _, role_definition_file = tempfile.mkstemp()
        with open(role_definition_file, 'w') as f:
            json.dump(self.sample_role_def, f)
        role_definition_file = role_definition_file.replace('\\', '\\\\')

        # action
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
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

        name = 'mysp'
        test_app_id = 'app_id_123'
        app = Application(app_id=test_app_id)
        faked_graph_client.applications.create.return_value = app
        sp = ServicePrincipal()
        faked_graph_client.service_principals.create.return_value = sp

        # action
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        result = create_service_principal_for_rbac(cmd, name, 12, skip_assignment=True)

        # assert
        self.assertEqual(result['displayName'], name)
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
        sp = ServicePrincipal()
        faked_graph_client.service_principals.create.return_value = sp

        # action
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        result = create_service_principal_for_rbac(cmd, name, cert=cert, years=2, skip_assignment=True)

        # assert
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
        cmd.cli_ctx = DummyCli()
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
        cmd.cli_ctx = DummyCli()

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
        cmd.cli_ctx = DummyCli()
        TestRoleMocked._common_rbac_err_polish_test_mock_setup(graph_client_mock, auth_client_mock,
                                                               'Insufficient privileges to complete the operation',
                                                               self.subscription_id)

        # action
        with self.assertRaises(CLIError) as context:
            create_service_principal_for_rbac(cmd, 'will-fail', skip_assignment=True)

        # assert we handled such error
        self.assertTrue('https://docs.microsoft.com/azure/azure-resource-manager/resource-group-create-service-principal-portal' in str(context.exception))

    @mock.patch('azure.cli.command_modules.role.custom._auth_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    def test_create_for_rbac_failed_with_regular_error(self, graph_client_mock, auth_client_mock):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
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

    def test_update_application_to_be_single_tenant(self):
        test_app_id = 'app_id_123'
        app = Application(app_id=test_app_id)
        setattr(app, 'additional_properties', {})
        instance = update_application(app, 'http://any-client',
                                      available_to_other_tenants=True)
        self.assertTrue(isinstance(instance, ApplicationUpdateParameters))
        self.assertEqual(instance.available_to_other_tenants, True)

    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    def test_list_sp_owner(self, graph_client_mock):

        test_sp_object_id = '11111111-2222-3333-4444-555555555555'
        test_sp_app_id = '11111111-2222-3333-4444-555555555555'
        test_user_object_id = '11111111-2222-3333-4444-555555555555'

        graph_client = mock.MagicMock()
        graph_client_mock.return_value = graph_client

        sp = mock.MagicMock()
        sp.object_id, sp.app_id = test_sp_object_id, test_sp_app_id

        user = mock.MagicMock()
        user.object_id = test_user_object_id

        graph_client.service_principals.list.return_value = [sp]
        graph_client.service_principals.list_owners.return_value = [user]

        # action
        res = list_service_principal_owners(mock.MagicMock(), test_sp_app_id)

        # assert
        graph_client.service_principals.list.assert_called_once()
        graph_client.service_principals.list_owners.assert_called_once()

        self.assertTrue(1 == len(res))
        self.assertTrue(test_user_object_id == res[0].object_id)

    @mock.patch('azure.cli.command_modules.role.custom._auth_client_factory', autospec=True)
    @mock.patch('knack.prompting.prompt_y_n', autospec=True)
    def test_role_assignment_delete_prompt(self, prompt_mock, client_mock):
        prompt_mock.return_value = False
        # action
        delete_role_assignments(mock.MagicMock())
        # assert
        prompt_mock.assert_called_once_with(mock.ANY, 'n')

    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    def test_role_list_app_owner(self, graph_client_mock):

        test_app_object_id = '11111111-2222-3333-4444-555555555555'
        test_app_app_id = '11111111-2222-3333-4444-555555555555'
        test_user_object_id = '11111111-2222-3333-4444-555555555555'

        graph_client = mock.MagicMock()
        graph_client_mock.return_value = graph_client

        app = mock.MagicMock()
        app.object_id, app.app_id = test_app_object_id, test_app_app_id

        user = mock.MagicMock()
        user.object_id = test_user_object_id

        graph_client.applications.list.return_value = [app]
        graph_client.applications.list_owners.return_value = [user]

        # action
        res = list_application_owners(mock.MagicMock(), test_app_app_id)

        # assert
        graph_client.applications.list.assert_called_once()
        graph_client.applications.list_owners.assert_called_once()

        self.assertTrue(1 == len(res))
        self.assertTrue(test_user_object_id == res[0].object_id)

    def test_get_object_stubs(self):
        graph_client = mock.MagicMock()
        assignees = [i for i in range(2001)]
        graph_client.objects.get_objects_by_object_ids.return_value = []

        # action
        _get_object_stubs(graph_client, assignees)

        # assert
        # we get called with right args
        self.assertEqual(graph_client.objects.get_objects_by_object_ids.call_count, 3)
        object_groups = []
        for i in range(0, 2001, 1000):
            object_groups.append([i for i in range(i, min(i + 1000, 2001))])

        for call, group in zip(graph_client.objects.get_objects_by_object_ids.call_args_list, object_groups):
            args, _ = call
            self.assertEqual(args[0].object_ids, group)

    @mock.patch('azure.cli.command_modules.role.custom._auth_client_factory')
    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory')
    @mock.patch('azure.cli.command_modules.role.custom._create_service_principal')
    @mock.patch('azure.cli.command_modules.role.custom.create_application')
    def test_create_for_rbac_retry(self, create_application_mock, create_service_principal_mock,
                                   graph_client_factory_mock, auth_client_factory_mock):
        graph_client_factory_mock.return_value.config.tenant_id = '00000001-0000-0000-0000-000000000000'
        create_application_mock.return_value.app_id = '00000000-0000-0000-0000-000000000000'
        create_service_principal_mock.side_effect = [
            # Mock replication exceptions
            Exception("The appId '00000000-0000-0000-0000-000000000000' of the service principal "
                      "does not reference a valid application object."),
            Exception("When using this permission, the backing application of the service principal being "
                      "created must in the local tenant"),
            # Success
            mock.MagicMock()
        ]
        # action
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        with mock.patch("time.sleep", lambda _: None):
            create_service_principal_for_rbac(cmd, skip_assignment=True)


class FakedError(object):  # pylint: disable=too-few-public-methods
    def __init__(self, message):
        self.message = message


if __name__ == '__main__':
    unittest.main()
