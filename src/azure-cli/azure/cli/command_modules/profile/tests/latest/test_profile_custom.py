# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import unittest
from unittest import mock

from azure.cli.command_modules.profile.custom import (
    list_subscriptions, get_access_token, login, logout, account_clear, _remove_adal_token_cache)

from azure.cli.core._profile import _TENANT_LEVEL_ACCOUNT_NAME
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

        timestamp = 1695270561
        datetime_local = '2023-09-21 04:29:21.000000'

        token_entry = {
            'accessToken': 'token123',
            'expires_on': timestamp,
            'expiresOn': datetime_local
        }
        get_raw_token_mock.return_value = (('bearer', 'token123', token_entry), 'sub123',  'tenant123')

        result = get_access_token(cmd)

        # assert
        get_raw_token_mock.assert_called_with(mock.ANY, None, None, None, None)
        expected_result = {
            'tokenType': 'bearer',
            'accessToken': 'token123',
            'expires_on': timestamp,
            'expiresOn': datetime_local,
            'subscription': 'sub123',
            'tenant': 'tenant123'
        }
        self.assertEqual(result, expected_result)

        # assert it takes customized resource, subscription
        resource = 'https://graph.microsoft.com/'
        subscription_id = '00000001-0000-0000-0000-000000000000'
        get_raw_token_mock.return_value = (('bearer', 'token123', token_entry), subscription_id, 'tenant123')
        result = get_access_token(cmd, subscription=subscription_id, resource=resource)
        get_raw_token_mock.assert_called_with(mock.ANY, resource, None, subscription_id, None)

        # assert it takes customized scopes
        get_access_token(cmd, scopes='https://graph.microsoft.com/.default')
        get_raw_token_mock.assert_called_with(mock.ANY, None, scopes='https://graph.microsoft.com/.default',
                                              subscription=None, tenant=None)

        # test get token with tenant
        tenant_id = '00000000-0000-0000-0000-000000000000'
        get_raw_token_mock.return_value = (('bearer', 'token123', token_entry), None, tenant_id)
        result = get_access_token(cmd, tenant=tenant_id)
        expected_result = {
            'tokenType': 'bearer',
            'accessToken': 'token123',
            'expires_on': timestamp,
            'expiresOn': datetime_local,
            'tenant': tenant_id
        }
        self.assertEqual(result, expected_result)
        get_raw_token_mock.assert_called_with(mock.ANY, None, None, None, tenant_id)

    @mock.patch('azure.cli.command_modules.profile.custom.Profile', autospec=True)
    def test_login_with_mi(self, profile_mock):
        invoked = []

        def login_with_managed_identity_mock(*args, **kwargs):
            invoked.append(True)

        # mock the instance
        profile_instance = mock.MagicMock()
        profile_instance.login_with_managed_identity = login_with_managed_identity_mock
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


class TestLoginSubscriptionFilter(unittest.TestCase):
    """Tests for custom.login() with --skip-subscription-discovery and --subscription parameters."""

    def test_skip_subscription_discovery_requires_tenant(self):
        """--skip-subscription-discovery without --tenant raises CLIError."""
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        with self.assertRaisesRegex(CLIError, "'--skip-subscription-discovery' requires '--tenant'"):
            login(cmd, skip_subscription_discovery=True)

    def test_skip_subscription_discovery_without_tenant_with_subscription(self):
        """--skip-subscription-discovery --subscription S without --tenant raises CLIError."""
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        with self.assertRaisesRegex(CLIError, "'--skip-subscription-discovery' requires '--tenant'"):
            login(cmd, skip_subscription_discovery=True, default_subscription='sub-id')

    @mock.patch('azure.cli.command_modules.profile._subscription_selector.SubscriptionSelector', autospec=True)
    @mock.patch('azure.cli.command_modules.profile.custom.Profile', autospec=True)
    def test_skip_subscription_discovery_bypasses_selector(self, profile_mock, selector_mock):
        """--skip-subscription-discovery should bypass the interactive selector."""
        tenant_id = 'test-tenant'
        profile_instance = mock.MagicMock()
        profile_instance.login.return_value = [
            {'id': tenant_id, 'name': _TENANT_LEVEL_ACCOUNT_NAME, 'isDefault': True,
             'environmentName': 'AzureCloud', 'tenantId': tenant_id}
        ]
        profile_mock.return_value = profile_instance

        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        cmd.cli_ctx.config = mock.MagicMock()
        cmd.cli_ctx.config.getboolean.return_value = True  # login_experience_v2 = True

        result = login(cmd, tenant=tenant_id, skip_subscription_discovery=True)

        # Assert selector was never instantiated
        selector_mock.assert_not_called()
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], _TENANT_LEVEL_ACCOUNT_NAME)

    @mock.patch('azure.cli.command_modules.profile._subscription_selector.SubscriptionSelector', autospec=True)
    @mock.patch('azure.cli.command_modules.profile.custom.Profile', autospec=True)
    def test_default_subscription_bypasses_selector(self, profile_mock, selector_mock):
        """--subscription should bypass the interactive selector even without --skip-subscription-discovery."""
        sub_id = 'target-sub-id'
        profile_instance = mock.MagicMock()
        profile_instance.login.return_value = [
            {'id': sub_id, 'name': 'Target Sub', 'isDefault': True,
             'environmentName': 'AzureCloud', 'tenantId': 'tenant1'},
            {'id': 'other-sub', 'name': 'Other Sub', 'isDefault': False,
             'environmentName': 'AzureCloud', 'tenantId': 'tenant1'}
        ]
        profile_mock.return_value = profile_instance

        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        cmd.cli_ctx.config = mock.MagicMock()
        cmd.cli_ctx.config.getboolean.return_value = False

        # Interactive login (no username) with --subscription
        result = login(cmd, tenant='tenant1', default_subscription=sub_id)

        # Assert selector was never instantiated
        selector_mock.assert_not_called()
        assert result is not None
        self.assertEqual(len(result), 2)
