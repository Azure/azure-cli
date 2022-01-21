# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import unittest
from unittest import mock

from azure.cli.command_modules.profile.custom import (
    list_subscriptions, get_access_token, login, logout, account_clear, _remove_adal_token_cache)

from azure.cli.core.mock import DummyCli
from knack.util import CLIError


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

        get_raw_token_mock.return_value = (['bearer', 'token123', {'expiresOn': '2100-01-01'}], 'sub123', 'tenant123')

        result = get_access_token(cmd)

        # assert
        get_raw_token_mock.assert_called_with(mock.ANY, None, None, None, None)
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
        get_raw_token_mock.assert_called_with(mock.ANY, resource, None, subscription_id, None)

        # assert it takes customized scopes
        get_access_token(cmd, scopes='https://graph.microsoft.com/.default')
        get_raw_token_mock.assert_called_with(mock.ANY, None, scopes='https://graph.microsoft.com/.default',
                                              subscription=None, tenant=None)

        # test get token with tenant
        tenant_id = '00000000-0000-0000-0000-000000000000'
        get_raw_token_mock.return_value = (['bearer', 'token123', {'expiresOn': '2100-01-01'}], None, tenant_id)
        result = get_access_token(cmd, tenant=tenant_id)
        expected_result = {
            'tokenType': 'bearer',
            'accessToken': 'token123',
            'expiresOn': '2100-01-01',
            'tenant': tenant_id
        }
        self.assertEqual(result, expected_result)
        get_raw_token_mock.assert_called_with(mock.ANY, None, None, None, tenant_id)

    @mock.patch('azure.cli.command_modules.profile.custom.Profile', autospec=True)
    def test_get_login(self, profile_mock):
        invoked = []

        def test_login(msi_port, identity_id=None):
            invoked.append(True)

        # mock the instance
        profile_instance = mock.MagicMock()
        profile_instance.login_with_managed_identity = test_login
        # mock the constructor
        profile_mock.return_value = profile_instance

        # action
        cmd = mock.MagicMock()
        login(cmd, identity=True)

        # assert
        self.assertTrue(invoked)

    def test_login_validate_tenant(self):
        from azure.cli.command_modules.profile._validators import validate_tenant

        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        namespace = mock.MagicMock()

        microsoft_tenant_id = '72f988bf-86f1-41af-91ab-2d7cd011db47'

        # Test tenant is unchanged for None
        namespace.tenant = None
        validate_tenant(cmd, namespace)
        self.assertEqual(namespace.tenant, None)

        # Test tenant is unchanged for GUID
        namespace.tenant = microsoft_tenant_id
        validate_tenant(cmd, namespace)
        self.assertEqual(namespace.tenant, microsoft_tenant_id)

        # Test tenant is resolved for canonical name
        namespace.tenant = "microsoft.onmicrosoft.com"
        validate_tenant(cmd, namespace)
        self.assertEqual(namespace.tenant, microsoft_tenant_id)

        # Test tenant is resolved for domain name
        namespace.tenant = "microsoft.com"
        validate_tenant(cmd, namespace)
        self.assertEqual(namespace.tenant, microsoft_tenant_id)

        # Test error is raised for non-existing tenant
        namespace.tenant = "non-existing-tenant"
        with self.assertRaisesRegex(CLIError, 'Failed to resolve tenant'):
            validate_tenant(cmd, namespace)

        # Test error is raised for non-existing tenant
        namespace.tenant = "non-existing-tenant.onmicrosoft.com"
        with self.assertRaisesRegex(CLIError, 'Failed to resolve tenant'):
            validate_tenant(cmd, namespace)

    @mock.patch('azure.cli.command_modules.profile.custom._remove_adal_token_cache', autospec=True)
    @mock.patch('azure.cli.command_modules.profile.custom.Profile', autospec=True)
    def test_logout(self, profile_mock, remove_adal_token_cache_mock):
        cmd = mock.MagicMock()

        profile_instance = mock.MagicMock()
        profile_instance.get_current_account_user.return_value = "user1"
        profile_mock.return_value = profile_instance

        # Log out without username
        logout(cmd)
        remove_adal_token_cache_mock.assert_called_once()
        profile_instance.get_current_account_user.assert_called_once()

        # Reset mock for next test
        remove_adal_token_cache_mock.reset_mock()
        profile_instance.get_current_account_user.reset_mock()

        # Log out with username
        logout(cmd, username='user2')
        remove_adal_token_cache_mock.assert_called_once()
        profile_instance.get_current_account_user.assert_not_called()
        profile_instance.logout.assert_called_with('user2')

    @mock.patch('azure.cli.command_modules.profile.custom._remove_adal_token_cache', autospec=True)
    @mock.patch('azure.cli.command_modules.profile.custom.Profile', autospec=True)
    def test_account_clear(self, profile_mock, remove_adal_token_cache_mock):
        cmd = mock.MagicMock()

        profile_instance = mock.MagicMock()
        profile_mock.return_value = profile_instance

        account_clear(cmd)

        remove_adal_token_cache_mock.assert_called_once()
        profile_instance.logout_all.assert_called_once()

    def test_remove_adal_token_cache(self):
        # If accessTokens.json doesn't exist
        assert not _remove_adal_token_cache()

        # If accessTokens.json exists
        from azure.cli.core._environment import get_config_dir
        adal_token_cache = os.path.join(get_config_dir(), 'accessTokens.json')
        with open(adal_token_cache, 'w') as f:
            f.write("test_token_cache")
        assert _remove_adal_token_cache()
        assert not os.path.exists(adal_token_cache)
