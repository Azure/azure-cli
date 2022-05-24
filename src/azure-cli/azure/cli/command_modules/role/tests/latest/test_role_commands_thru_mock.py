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

from azure.mgmt.authorization.models import RoleDefinition
from knack.util import CLIError

from azure.cli.command_modules.role.custom import (create_role_definition,
                                                   update_role_definition,
                                                   create_service_principal_for_rbac,
                                                   reset_application_credential,
                                                   _try_x509_pem,
                                                   _get_object_stubs,
                                                   list_service_principal_owners,
                                                   list_application_owners,
                                                   delete_role_assignments)
from azure.cli.command_modules.role._msgrpah import GraphError
from azure.cli.core.mock import DummyCli

# pylint: disable=line-too-long

MOCKED_TENANT_ID = '00000001-0000-0000-0000-000000000000'


MOCKED_APP_APP_ID = '00000000-0000-0000-0000-000000000001'
MOCKED_APP_ID = '00000000-0000-0000-0000-000000000002'

MOCKED_APP_DISPLAY_NAME = 'mocked_app'
MOCKED_PASSWORD = 'graph_service_generated_password'
MOCKED_CREDENTIAL_DISPLAY_NAME = "test-credential-display-name"
MOCKED_PASSWORD_KEY_ID = "f0b0b335-1d71-4883-8f98-567911bfdca6"
MOCKED_KEY_KEY_ID = "d35f12d5-1fab-4fe9-86e5-ed072e3d2288"

MOCKED_USER_ID = 'mocked_user_id'

MOCKED_APP = {
    'id': MOCKED_APP_ID,
    'appId': MOCKED_APP_APP_ID,
    'displayName': MOCKED_APP_DISPLAY_NAME,
    "passwordCredentials": [
        {
            "customKeyIdentifier": None,
            "displayName": MOCKED_CREDENTIAL_DISPLAY_NAME,
            "endDateTime": "2022-11-30T10:01:21Z",
            "hint": "Z3Q",
            "keyId": MOCKED_PASSWORD_KEY_ID,
            "secretText": None,
            "startDateTime": "2021-11-30T10:01:21Z"
        }
    ],
    "keyCredentials": [
        {
            "customKeyIdentifier": "A90481E4E00F015B837330A27790E67C28A06E46",
            "displayName": "CN=CLI-Login",
            "endDateTime": "2023-05-07T05:39:54Z",
            "key": None,
            "keyId": MOCKED_KEY_KEY_ID,
            "startDateTime": "2022-05-07T05:39:54Z",
            "type": "AsymmetricX509Cert",
            "usage": "Verify"
        }
    ],
}

MOCKED_SP = {
    'id': '00000000-0000-0000-0000-000000000003',
    'appId': MOCKED_APP_APP_ID
}

# Example from https://docs.microsoft.com/en-us/graph/api/serviceprincipal-addpassword
MOCKED_ADD_PASSWORD_RESULT = {
    "customKeyIdentifier": None,
    "endDateTime": "2021-09-09T19:50:29.3086381Z",
    "keyId": MOCKED_PASSWORD_KEY_ID,
    "startDateTime": "2019-09-09T19:50:29.3086381Z",
    "secretText": MOCKED_PASSWORD,
    "hint": "[6g",
    "displayName": "Password friendly name"
}


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

        faked_graph_client.application_create.return_value = MOCKED_APP
        faked_graph_client.application_add_password.return_value = {'secretText': MOCKED_PASSWORD}
        faked_graph_client.service_principal_create.return_value = MOCKED_SP

        # action
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        result = create_service_principal_for_rbac(cmd, MOCKED_APP_DISPLAY_NAME, 12)

        # assert
        self.assertEqual(result['displayName'], MOCKED_APP_DISPLAY_NAME)
        self.assertEqual(result['appId'], MOCKED_APP_APP_ID)
        self.assertEqual(result['password'], MOCKED_PASSWORD)

    @mock.patch('azure.cli.command_modules.role.custom._auth_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.role.custom.logger', autospec=True)
    def test_create_for_rbac_use_cert_date(self, logger_mock, graph_client_mock, auth_client_mock):
        import OpenSSL.crypto

        def mock_app_create(parameters):
            end_date = parameters['keyCredentials'][0]['endDateTime']
            # Check the cert's expiration time
            self.assertEqual(end_date, '2018-04-21T18:27:50Z')
            return MOCKED_APP

        faked_role_client = mock.MagicMock()
        auth_client_mock.return_value = faked_role_client
        faked_role_client.config.subscription_id = self.subscription_id
        faked_graph_client = mock.MagicMock()
        graph_client_mock.return_value = faked_graph_client

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        cert_file = os.path.join(curr_dir, 'cert.pem').replace('\\', '\\\\')
        with open(cert_file) as f:
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, f.read())

        faked_graph_client.application_create.side_effect = mock_app_create
        faked_graph_client.service_principal_create.return_value = MOCKED_SP

        # action
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        result = create_service_principal_for_rbac(cmd, MOCKED_APP_DISPLAY_NAME, cert=cert, years=2)

        # assert
        self.assertEqual(result['appId'], MOCKED_APP_APP_ID)
        self.assertTrue(logger_mock.warning.called)  # we should warn 'years' will be dropped
        self.assertTrue(faked_graph_client.application_create.called)

    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    def test_reset_credentials_password(self, graph_client_mock):

        def add_password_mock(id, body):
            self.assertEqual(id, MOCKED_APP_ID)
            self.assertEqual(MOCKED_CREDENTIAL_DISPLAY_NAME, body['passwordCredential']['displayName'])
            return MOCKED_ADD_PASSWORD_RESULT

        def remove_password_mock(id, body):
            self.assertEqual(id, MOCKED_APP_ID)
            self.assertEqual(MOCKED_PASSWORD_KEY_ID, body['keyId'])

        faked_graph_client = mock.MagicMock()
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()

        graph_client_mock.return_value = faked_graph_client
        faked_graph_client.tenant = MOCKED_TENANT_ID
        faked_graph_client.application_list.return_value = [MOCKED_APP]
        faked_graph_client.application_get.side_effect = [MOCKED_APP]
        faked_graph_client.application_add_password.side_effect = add_password_mock
        faked_graph_client.application_remove_password.side_effect = remove_password_mock

        # action
        result = reset_application_credential(cmd, faked_graph_client, MOCKED_APP_APP_ID,
                                              display_name=MOCKED_CREDENTIAL_DISPLAY_NAME)

        # assert
        faked_graph_client.application_add_password.assert_called_once()
        faked_graph_client.application_remove_password.assert_called_once()
        assert result == {
            'appId': MOCKED_APP_APP_ID,
            'password': MOCKED_PASSWORD,
            'tenant': MOCKED_TENANT_ID
        }

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

        def application_patch_mock(id, body):
            patch_invoked[0] = True
            self.assertEqual(id, MOCKED_APP_ID)
            self.assertEqual(2, len(body['keyCredentials']))
            self.assertEqual(body['keyCredentials'][0]['keyId'], MOCKED_KEY_KEY_ID)
            self.assertTrue(body['keyCredentials'][1]['key'])
            self.assertEqual(body['keyCredentials'][1]['type'], 'AsymmetricX509Cert')
            self.assertEqual(body['keyCredentials'][1]['usage'], 'Verify')

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
        faked_graph_client.tenant = MOCKED_TENANT_ID
        faked_graph_client.application_list.return_value = [MOCKED_APP]
        faked_graph_client.application_get.side_effect = [MOCKED_APP]
        faked_graph_client.application_patch.side_effect = application_patch_mock

        # action
        result = reset_application_credential(cmd, faked_graph_client, MOCKED_APP_APP_ID, cert=test_cert, append=True,
                                              display_name=MOCKED_CREDENTIAL_DISPLAY_NAME)

        # assert
        faked_graph_client.application_patch.assert_called_once()
        assert result == {
            'appId': MOCKED_APP_APP_ID,
            'password': None,
            'tenant': MOCKED_TENANT_ID
        }

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
            create_service_principal_for_rbac(cmd, 'will-fail')

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
        with self.assertRaises(GraphError):
            create_service_principal_for_rbac(cmd, 'will-fail')

    @staticmethod
    def _common_rbac_err_polish_test_mock_setup(graph_client_mock, auth_client_mock, error_msg, subscription_id):
        faked_role_client = mock.MagicMock()
        faked_role_client.config.subscription_id = subscription_id
        auth_client_mock.return_value = faked_role_client
        faked_graph_client = mock.MagicMock()
        graph_client_mock.return_value = faked_graph_client

        faked_graph_client.application_create.side_effect = GraphError(error_msg, None)

    @mock.patch('azure.cli.command_modules.role.custom._graph_client_factory', autospec=True)
    def test_list_sp_owner(self, graph_client_mock):
        graph_client = mock.MagicMock()
        graph_client_mock.return_value = graph_client

        user = {
            "id": MOCKED_USER_ID
        }

        graph_client.service_principal_list.return_value = [MOCKED_SP]
        graph_client.service_principal_owner_list.return_value = [user]

        # action
        result = list_service_principal_owners(graph_client, MOCKED_APP_APP_ID)

        # assert
        graph_client.service_principal_list.assert_called_once()
        graph_client.service_principal_owner_list.assert_called_once()

        assert len(result) == 1
        assert result[0]['id'] == MOCKED_USER_ID

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
        graph_client = mock.MagicMock()
        graph_client_mock.return_value = graph_client

        user = {
            "id": MOCKED_USER_ID
        }

        graph_client.application_list.return_value = [MOCKED_APP]
        graph_client.application_owner_list.return_value = [user]

        # action
        result = list_application_owners(graph_client, MOCKED_APP_APP_ID)

        # assert
        graph_client.application_list.assert_called_once()
        graph_client.application_owner_list.assert_called_once()

        assert len(result) == 1
        assert result[0]['id'] == MOCKED_USER_ID

    def test_get_object_stubs(self):
        graph_client = mock.MagicMock()
        assignees = [i for i in range(2001)]
        graph_client.directory_object_get_by_ids.return_value = []

        # action
        _get_object_stubs(graph_client, assignees)

        # assert
        # we get called with right args
        self.assertEqual(graph_client.directory_object_get_by_ids.call_count, 3)
        object_groups = []
        for i in range(0, 2001, 1000):
            object_groups.append([i for i in range(i, min(i + 1000, 2001))])

        # object_groups is
        # [
        #   [0, 1, 2, ..., 999],
        #   [1000, 1001, 1002, ..., 1999],
        #   [2000]
        # ]

        for call, group in zip(graph_client.directory_object_get_by_ids.call_args_list, object_groups):
            args, _ = call
            self.assertEqual(args[0]['ids'], group)

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


if __name__ == '__main__':
    unittest.main()
