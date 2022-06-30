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


# The test access token is created using following commands.

# 1. Create a new user with tenant admin account.
#   az ad user create --display-name "Azure CLI Test User" --user-principal-name azure-cli-test-user@AzureSDKTeam.onmicrosoft.com --password xxx

# 2. Use the new user account to log in and get an access token. You may do this on another machine or WSL.
# MAKE SURE to redact the signature (3rd) segment of the token to invalidate it.
#   az login --username azure-cli-test-user@AzureSDKTeam.onmicrosoft.com --password xxx --allow-no-subscriptions
#   az account get-access-token --query accessToken --output tsv

# 3. At last, use the admin account to delete the user.
#   az ad user delete --id azure-cli-test-user@AzureSDKTeam.onmicrosoft.com
TEST_USER_ACCESS_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6ImpTMVhvMU9XRGpfNTJ2YndHTmd2UU8yVnpNYyIsImtpZCI6ImpTMVhvMU9XRGpfNTJ2YndHTmd2UU8yVnpNYyJ9.eyJhdWQiOiJodHRwczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81NDgyNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEvIiwiaWF0IjoxNjU0NjcxNDg2LCJuYmYiOjE2NTQ2NzE0ODYsImV4cCI6MTY1NDY3NTQzMiwiYWNyIjoiMSIsImFpbyI6IkFUUUF5LzhUQUFBQVgzeCtvV092RVR6alY5Nm1hNnVqeEp3OWFUenJGWHV4SnFrRmFRb3ZtL1I3WUdBVjA5SDFCVmluOUVNQXVYeVIiLCJhbXIiOlsicHdkIl0sImFwcGlkIjoiMDRiMDc3OTUtOGRkYi00NjFhLWJiZWUtMDJmOWUxYmY3YjQ2IiwiYXBwaWRhY3IiOiIwIiwiaXBhZGRyIjoiMTY3LjIyMC4yNTUuMjciLCJuYW1lIjoiQXp1cmUgQ0xJIFRlc3QgVXNlciIsIm9pZCI6IjY2NTY2YjBmLTg1OTAtNDQxYy1hYmJhLWQ4ZWQxNjQ2YTEwYiIsInB1aWQiOiIxMDAzMjAwMjAzNDREQzM5IiwicmgiOiIwLkFUY0FJbXVDVk5ZNHNrLTYyYmU1T2o2Y1drWklmM2tBdXRkUHVrUGF3ZmoyTUJNM0FIZy4iLCJzY3AiOiJ1c2VyX2ltcGVyc29uYXRpb24iLCJzdWIiOiJiWVNQZXpNeHF5TDQxRHBBdWhxRjJ3ZGpoLWhJbm5SOFpCeFRrTGw2V21RIiwidGlkIjoiNTQ4MjZiMjItMzhkNi00ZmIyLWJhZDktYjdiOTNhM2U5YzVhIiwidW5pcXVlX25hbWUiOiJhenVyZS1jbGktdGVzdC11c2VyQEF6dXJlU0RLVGVhbS5vbm1pY3Jvc29mdC5jb20iLCJ1cG4iOiJhenVyZS1jbGktdGVzdC11c2VyQEF6dXJlU0RLVGVhbS5vbm1pY3Jvc29mdC5jb20iLCJ1dGkiOiIydzVNZDBPaE4wNkhhR2ZmTEQxQkFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyJiNzlmYmY0ZC0zZWY5LTQ2ODktODE0My03NmIxOTRlODU1MDkiXSwieG1zX3RjZHQiOjE0MTIyMDY4NDB9.redacted'


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

        get_raw_token_mock.return_value = (['bearer', TEST_USER_ACCESS_TOKEN, {'expiresOn': '2100-01-01'}], 'sub123', 'tenant123')

        result = get_access_token(cmd)

        # assert
        get_raw_token_mock.assert_called_with(mock.ANY, None, None, None, None)
        expected_result = {
            'tokenType': 'bearer',
            'accessToken': TEST_USER_ACCESS_TOKEN,
            'expiresOn': '2100-01-01',
            'subscription': 'sub123',
            'tenant': 'tenant123'
        }
        self.assertEqual(result, expected_result)

        # assert it takes customized resource, subscription
        resource = 'https://graph.microsoft.com/'
        subscription_id = '00000001-0000-0000-0000-000000000000'
        get_raw_token_mock.return_value = (['bearer', TEST_USER_ACCESS_TOKEN, {'expiresOn': '2100-01-01'}], subscription_id,
                                           'tenant123')
        result = get_access_token(cmd, subscription=subscription_id, resource=resource)
        get_raw_token_mock.assert_called_with(mock.ANY, resource, None, subscription_id, None)

        # assert it takes customized scopes
        get_access_token(cmd, scopes='https://graph.microsoft.com/.default')
        get_raw_token_mock.assert_called_with(mock.ANY, None, scopes='https://graph.microsoft.com/.default',
                                              subscription=None, tenant=None)

        # test get token with tenant
        tenant_id = '00000000-0000-0000-0000-000000000000'
        get_raw_token_mock.return_value = (['bearer', TEST_USER_ACCESS_TOKEN, {'expiresOn': '2100-01-01'}], None, tenant_id)
        result = get_access_token(cmd, tenant=tenant_id)
        expected_result = {
            'tokenType': 'bearer',
            'accessToken': TEST_USER_ACCESS_TOKEN,
            'expiresOn': '2100-01-01',
            'tenant': tenant_id
        }
        self.assertEqual(result, expected_result)
        get_raw_token_mock.assert_called_with(mock.ANY, None, None, None, tenant_id)

        # Test showing claims of the access token
        result = get_access_token(cmd, show_claims=True)
        assert result['oid'] == '66566b0f-8590-441c-abba-d8ed1646a10b'
        assert result['tid'] == '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a'
        assert result['name'] == 'Azure CLI Test User'
        assert result['upn'] == 'azure-cli-test-user@AzureSDKTeam.onmicrosoft.com'

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
