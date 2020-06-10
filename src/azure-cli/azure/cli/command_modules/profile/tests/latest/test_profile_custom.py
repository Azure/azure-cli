# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from azure.cli.command_modules.profile.custom import list_subscriptions, get_access_token, login
from azure.cli.core.mock import DummyCli


class ProfileCommandTest(unittest.TestCase):
    @mock.patch('azure.cli.core.api.load_subscriptions', autospec=True)
    @mock.patch('azure.cli.command_modules.profile.custom.logger', autospec=True)
    def test_list_only_enabled_one(self, logger_mock, load_subscription_mock):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        sub1 = {'state': 'Enabled'}
        sub2 = {'state': 'Overdued'}
        load_subscription_mock.return_value = [sub1, sub2]

        # list all
        self.assertEqual(2, len(list_subscriptions(cmd, all=True)))
        self.assertTrue(not logger_mock.warning.called)
        # list only enabled one
        result = list_subscriptions(cmd)
        self.assertEqual(1, len(result))
        self.assertEqual('Enabled', result[0]['state'])
        logger_mock.warning.assert_called_once_with(mock.ANY)

    @mock.patch('azure.cli.core._profile.Profile.get_raw_token', autospec=True)
    def test_get_raw_token(self, get_raw_token_mock):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()

        # arrange
        get_raw_token_mock.return_value = (['bearer', 'token123', {'expiresOn': '2100-01-01'}], 'sub123', 'tenant123')

        # action
        result = get_access_token(cmd)

        # assert
        get_raw_token_mock.assert_called_with(mock.ANY, 'https://management.core.windows.net/', None, None)
        expected_result = {
            'tokenType': 'bearer',
            'accessToken': 'token123',
            'expiresOn': '2100-01-01',
            'subscription': 'sub123',
            'tenant': 'tenant123'
        }
        self.assertEqual(result, expected_result)

        # assert it takes customized resource, subscription
        resource = 'https://graph.microsoft.com/'
        subscription_id = '00000001-0000-0000-0000-000000000000'
        get_raw_token_mock.return_value = (['bearer', 'token123', {'expiresOn': '2100-01-01'}], subscription_id,
                                           'tenant123')
        result = get_access_token(cmd, subscription=subscription_id, resource=resource)
        get_raw_token_mock.assert_called_with(mock.ANY, resource, subscription_id, None)
        expected_result = {
            'tokenType': 'bearer',
            'accessToken': 'token123',
            'expiresOn': '2100-01-01',
            'subscription': subscription_id,
            'tenant': 'tenant123'
        }
        self.assertEqual(result, expected_result)

        # test get token with tenant
        tenant_id = '00000000-0000-0000-0000-000000000000'
        get_raw_token_mock.return_value = (['bearer', 'token123', {'expiresOn': '2100-01-01'}], None, tenant_id)
        result = get_access_token(cmd, tenant=tenant_id)
        get_raw_token_mock.assert_called_with(mock.ANY, 'https://management.core.windows.net/', None, tenant_id)
        expected_result = {
            'tokenType': 'bearer',
            'accessToken': 'token123',
            'expiresOn': '2100-01-01',  # subscription shouldn't be present
            'tenant': tenant_id
        }
        self.assertEqual(result, expected_result)

    @mock.patch('azure.cli.command_modules.profile.custom.Profile', autospec=True)
    def test_get_login(self, profile_mock):
        invoked = []

        def test_login(msi_port, identity_id=None):
            invoked.append(True)

        # mock the instance
        profile_instance = mock.MagicMock()
        profile_instance.find_subscriptions_in_vm_with_msi = test_login
        # mock the constructor
        profile_mock.return_value = profile_instance

        # action
        cmd = mock.MagicMock()
        login(cmd, identity=True)

        # assert
        self.assertTrue(invoked)
