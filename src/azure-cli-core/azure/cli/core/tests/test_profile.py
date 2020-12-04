# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
import json
import os
import sys
import unittest
import mock
import re
import datetime

from copy import deepcopy

from adal import AdalError

from azure.cli.core._profile import (Profile, SubscriptionFinder, _USE_VENDORED_SUBSCRIPTION_SDK,
                                     _detect_adfs_authority)
if _USE_VENDORED_SUBSCRIPTION_SDK:
    from azure.cli.core.vendored_sdks.subscriptions.models import \
        (SubscriptionState, Subscription, SubscriptionPolicies, SpendingLimit, ManagedByTenant)
else:
    from azure.mgmt.resource.subscriptions.models import \
        (SubscriptionState, Subscription, SubscriptionPolicies, SpendingLimit, ManagedByTenant)

from azure.cli.core.mock import DummyCli
from azure.identity import AuthenticationRecord

from knack.util import CLIError


class PublicClientApplicationMock(mock.MagicMock):

    def get_accounts(self, username):
        return [account for account in TestProfile.msal_accounts if account['username'] == username]


class TestProfile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tenant_id = 'microsoft.com'
        cls.user1 = 'foo@foo.com'
        cls.id1 = 'subscriptions/1'
        cls.display_name1 = 'foo account'
        cls.home_account_id = "00000003-0000-0000-0000-000000000000.00000003-0000-0000-0000-000000000000"
        cls.client_id = "00000003-0000-0000-0000-000000000000"
        cls.authentication_record = AuthenticationRecord(cls.tenant_id, cls.client_id,
                                                         "https://login.microsoftonline.com", cls.home_account_id,
                                                         cls.user1)
        cls.state1 = SubscriptionState.enabled
        cls.managed_by_tenants = [ManagedByTenantStub('00000003-0000-0000-0000-000000000000'),
                                  ManagedByTenantStub('00000004-0000-0000-0000-000000000000')]
        # Dummy Subscription from SDK azure.mgmt.resource.subscriptions.v2019_06_01.operations._subscriptions_operations.SubscriptionsOperations.list
        # tenant_id denotes home tenant
        # Must be deepcopied before used as mock_arm_client.subscriptions.list.return_value
        cls.subscription1_raw = SubscriptionStub(cls.id1,
                                                 cls.display_name1,
                                                 cls.state1,
                                                 tenant_id=cls.tenant_id,
                                                 managed_by_tenants=cls.managed_by_tenants)

        cls.subscription1_output = [{'environmentName': 'AzureCloud',
                                     'homeTenantId': 'microsoft.com',
                                     'id': '1',
                                     'isDefault': True,
                                     'managedByTenants': [{'tenantId': '00000003-0000-0000-0000-000000000000'},
                                                          {'tenantId': '00000004-0000-0000-0000-000000000000'}],
                                     'name': 'foo account',
                                     'state': 'Enabled',
                                     'tenantId': 'microsoft.com',
                                     'user': {
                                         'name': 'foo@foo.com',
                                         'type': 'user'
                                     }}]

        # Dummy result of azure.cli.core._profile.SubscriptionFinder._find_using_specific_tenant
        # It has home_tenant_id which is mapped from tenant_id. tenant_id now denotes token tenant.
        cls.subscription1 = SubscriptionStub(cls.id1,
                                             cls.display_name1,
                                             cls.state1,
                                             tenant_id=cls.tenant_id,
                                             managed_by_tenants=cls.managed_by_tenants,
                                             home_tenant_id=cls.tenant_id)
        # Dummy result of azure.cli.core._profile.Profile._normalize_properties
        cls.subscription1_normalized = {
            'environmentName': 'AzureCloud',
            'id': '1',
            'name': cls.display_name1,
            'state': cls.state1.value,
            'user': {
                'name': cls.user1,
                'type': 'user'
            },
            'isDefault': False,
            'tenantId': cls.tenant_id,
            'homeTenantId': cls.tenant_id,
            'managedByTenants': [
                {
                    "tenantId": "00000003-0000-0000-0000-000000000000"
                },
                {
                    "tenantId": "00000004-0000-0000-0000-000000000000"
                }
            ],
        }

        cls.raw_token1 = 'some...secrets'
        cls.token_entry1 = {
            "_clientId": "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
            "resource": "https://management.core.windows.net/",
            "tokenType": "Bearer",
            "expiresOn": "2016-03-31T04:26:56.610Z",
            "expiresIn": 3599,
            "identityProvider": "live.com",
            "_authority": "https://login.microsoftonline.com/common",
            "isMRRT": True,
            "refreshToken": "faked123",
            "accessToken": cls.raw_token1,
            "userId": cls.user1
        }
        from azure.core.credentials import AccessToken
        import time
        cls.access_token = AccessToken(cls.raw_token1, int(cls.token_entry1['expiresIn'] + time.time()))
        cls.user2 = 'bar@bar.com'
        cls.id2 = 'subscriptions/2'
        cls.display_name2 = 'bar account'
        cls.state2 = SubscriptionState.past_due
        cls.subscription2_raw = SubscriptionStub(cls.id2,
                                                 cls.display_name2,
                                                 cls.state2,
                                                 tenant_id=cls.tenant_id)
        cls.subscription2 = SubscriptionStub(cls.id2,
                                             cls.display_name2,
                                             cls.state2,
                                             tenant_id=cls.tenant_id,
                                             home_tenant_id=cls.tenant_id)
        cls.subscription2_normalized = {
            'environmentName': 'AzureCloud',
            'id': '2',
            'name': cls.display_name2,
            'state': cls.state2.value,
            'user': {
                'name': cls.user2,
                'type': 'user'
            },
            'isDefault': False,
            'tenantId': cls.tenant_id,
            'homeTenantId': cls.tenant_id,
            'managedByTenants': [],
        }
        cls.test_msi_tenant = '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a'
        cls.test_msi_access_token = ('eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IlZXVkljMVdEMVRrc2JiMzAxc2FzTTVrT3E1'
                                     'USIsImtpZCI6IlZXVkljMVdEMVRrc2JiMzAxc2FzTTVrT3E1USJ9.eyJhdWQiOiJodHRwczovL21hbmF'
                                     'nZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81NDg'
                                     'yNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEvIiwiaWF0IjoxNTAzMzU0ODc2LCJuYmYiOjE'
                                     '1MDMzNTQ4NzYsImV4cCI6MTUwMzM1ODc3NiwiYWNyIjoiMSIsImFpbyI6IkFTUUEyLzhFQUFBQTFGL1k'
                                     '0VVR3bFI1Y091QXJxc1J0OU5UVVc2MGlsUHZna0daUC8xczVtdzg9IiwiYW1yIjpbInB3ZCJdLCJhcHB'
                                     'pZCI6IjA0YjA3Nzk1LThkZGItNDYxYS1iYmVlLTAyZjllMWJmN2I0NiIsImFwcGlkYWNyIjoiMCIsImV'
                                     'fZXhwIjoyNjI4MDAsImZhbWlseV9uYW1lIjoic2RrIiwiZ2l2ZW5fbmFtZSI6ImFkbWluMyIsImdyb3V'
                                     'wcyI6WyJlNGJiMGI1Ni0xMDE0LTQwZjgtODhhYi0zZDhhOGNiMGUwODYiLCI4YTliMTYxNy1mYzhkLTR'
                                     'hYTktYTQyZi05OTg2OGQzMTQ2OTkiLCI1NDgwMzkxNy00YzcxLTRkNmMtOGJkZi1iYmQ5MzEwMTBmOGM'
                                     'iXSwiaXBhZGRyIjoiMTY3LjIyMC4xLjIzNCIsIm5hbWUiOiJhZG1pbjMiLCJvaWQiOiJlN2UxNThkMy0'
                                     '3Y2RjLTQ3Y2QtODgyNS01ODU5ZDdhYjJiNTUiLCJwdWlkIjoiMTAwMzNGRkY5NUQ0NEU4NCIsInNjcCI'
                                     '6InVzZXJfaW1wZXJzb25hdGlvbiIsInN1YiI6ImhRenl3b3FTLUEtRzAySTl6ZE5TRmtGd3R2MGVwZ2l'
                                     'WY1Vsdm1PZEZHaFEiLCJ0aWQiOiI1NDgyNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEiLCJ'
                                     '1bmlxdWVfbmFtZSI6ImFkbWluM0BBenVyZVNES1RlYW0ub25taWNyb3NvZnQuY29tIiwidXBuIjoiYWR'
                                     'taW4zQEF6dXJlU0RLVGVhbS5vbm1pY3Jvc29mdC5jb20iLCJ1dGkiOiJuUEROYm04UFkwYUdELWhNeWx'
                                     'rVEFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyI2MmU5MDM5NC02OWY1LTQyMzctOTE5MC0wMTIxNzcxNDV'
                                     'lMTAiXX0.Pg4cq0MuP1uGhY_h51ZZdyUYjGDUFgTW2EfIV4DaWT9RU7GIK_Fq9VGBTTbFZA0pZrrmP-z'
                                     '7DlN9-U0A0nEYDoXzXvo-ACTkm9_TakfADd36YlYB5aLna-yO0B7rk5W9ANelkzUQgRfidSHtCmV6i4V'
                                     'e-lOym1sH5iOcxfIjXF0Tp2y0f3zM7qCq8Cp1ZxEwz6xYIgByoxjErNXrOME5Ld1WizcsaWxTXpwxJn_'
                                     'Q8U2g9kXHrbYFeY2gJxF_hnfLvNKxUKUBnftmyYxZwKi0GDS0BvdJnJnsqSRSpxUx__Ra9QJkG1IaDzj'
                                     'ZcSZPHK45T6ohK9Hk9ktZo0crVl7Tmw')
        cls.test_user_msi_access_token = ('eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IlNzWnNCTmhaY0YzUTlTNHRycFFCVE'
                                          'J5TlJSSSIsImtpZCI6IlNzWnNCTmhaY0YzUTlTNHRycFFCVEJ5TlJSSSJ9.eyJhdWQiOiJodHR'
                                          'wczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldCIsImlzcyI6Imh0dHBzOi8vc3RzLndpbm'
                                          'Rvd3MubmV0LzU0ODI2YjIyLTM4ZDYtNGZiMi1iYWQ5LWI3YjkzYTNlOWM1YS8iLCJpYXQiOjE1O'
                                          'TE3ODM5MDQsIm5iZiI6MTU5MTc4MzkwNCwiZXhwIjoxNTkxODcwNjA0LCJhaW8iOiI0MmRnWUZE'
                                          'd2JsZmR0WmYxck8zeGlMcVdtOU5MQVE9PSIsImFwcGlkIjoiNjJhYzQ5ZTYtMDQzOC00MTJjLWJ'
                                          'kZjUtNDg0ZTdkNDUyOTM2IiwiYXBwaWRhY3IiOiIyIiwiaWRwIjoiaHR0cHM6Ly9zdHMud2luZG'
                                          '93cy5uZXQvNTQ4MjZiMjItMzhkNi00ZmIyLWJhZDktYjdiOTNhM2U5YzVhLyIsIm9pZCI6ImQ4M'
                                          'zRjNjZmLTNhZjgtNDBiNy1iNDYzLWViZGNlN2YzYTgyNyIsInN1YiI6ImQ4MzRjNjZmLTNhZjgt'
                                          'NDBiNy1iNDYzLWViZGNlN2YzYTgyNyIsInRpZCI6IjU0ODI2YjIyLTM4ZDYtNGZiMi1iYWQ5LWI'
                                          '3YjkzYTNlOWM1YSIsInV0aSI6Ild2YjFyVlBQT1V5VjJDYmNyeHpBQUEiLCJ2ZXIiOiIxLjAiLC'
                                          'J4bXNfbWlyaWQiOiIvc3Vic2NyaXB0aW9ucy8wYjFmNjQ3MS0xYmYwLTRkZGEtYWVjMy1jYjkyNz'
                                          'JmMDk1OTAvcmVzb3VyY2Vncm91cHMvcWlhbndlbnMvcHJvdmlkZXJzL01pY3Jvc29mdC5NYW5hZ2'
                                          'VkSWRlbnRpdHkvdXNlckFzc2lnbmVkSWRlbnRpdGllcy9xaWFud2VuaWRlbnRpdHkifQ.nAxWA5_'
                                          'qTs_uwGoziKtDFAqxlmYSlyPGqAKZ8YFqFfm68r5Ouo2x2PztAv2D71L-j8B3GykNgW-2yhbB-z2'
                                          'h53dgjG2TVoeZjhV9DOpSJ06kLAeH-nskGxpBFf7se1qohlU7uyctsUMQWjXVUQbTEanJzj_IH-Y'
                                          '47O3lvM4Yrliz5QUApm63VF4EhqNpNvb5w0HkuB72SJ0MKJt5VdQqNcG077NQNoiTJ34XVXkyNDp'
                                          'I15y0Cj504P_xw-Dpvg-hmEbykjFMIaB8RoSrp3BzYjNtJh2CHIuWhXF0ngza2SwN2CXK0Vpn5Za'
                                          'EvZdD57j3h8iGE0Tw5IzG86uNS2AQ0A')

        cls.msal_accounts = [
            {
                'home_account_id': '182c0000-0000-0000-0000-000000000000.54820000-0000-0000-0000-000000000000',
                'environment': 'login.microsoftonline.com',
                'realm': 'organizations',
                'local_account_id': '182c0000-0000-0000-0000-000000000000',
                'username': cls.user1,
                'authority_type': 'MSSTS'
            }, {
                'home_account_id': '182c0000-0000-0000-0000-000000000000.54820000-0000-0000-0000-000000000000',
                'environment': 'login.microsoftonline.com',
                'realm': '54820000-0000-0000-0000-000000000000',
                'local_account_id': '182c0000-0000-0000-0000-000000000000',
                'username': cls.user1,
                'authority_type': 'MSSTS'
            }, {
                'home_account_id': 'c7970000-0000-0000-0000-000000000000.54820000-0000-0000-0000-000000000000',
                'environment': 'login.microsoftonline.com',
                'realm': 'organizations',
                'local_account_id': 'c7970000-0000-0000-0000-000000000000',
                'username': cls.user2,
                'authority_type': 'MSSTS'
            }, {
                'home_account_id': 'c7970000-0000-0000-0000-000000000000.54820000-0000-0000-0000-000000000000',
                'environment': 'login.microsoftonline.com',
                'realm': '54820000-0000-0000-0000-000000000000',
                'local_account_id': 'c7970000-0000-0000-0000-000000000000',
                'username': cls.user2,
                'authority_type': 'MSSTS'
            }]

        cls.msal_scopes = ['https://foo/.default']

        cls.service_principal_id = "00000001-0000-0000-0000-000000000000"
        cls.service_principal_secret = "test_secret"
        cls.service_principal_tenant_id = "00000001-0000-0000-0000-000000000000"

    @mock.patch('azure.identity.InteractiveBrowserCredential.authenticate', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    @mock.patch('azure.cli.core._profile.can_launch_browser', autospec=True, return_value=True)
    def test_login_with_interactive_browser(self, can_launch_browser_mock, app_mock, authenticate_mock):
        authenticate_mock.return_value = self.authentication_record

        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        subs = profile.login(True, None, None, False, None, use_device_code=False,
                             allow_no_subscriptions=False, subscription_finder=finder)

        # assert
        self.assertEqual(self.subscription1_output, subs)

    @mock.patch('azure.identity.UsernamePasswordCredential.authenticate', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_login_with_username_password_for_tenant(self, app_mock, authenticate_mock):
        authenticate_mock.return_value = self.authentication_record
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.side_effect = ValueError("'tenants.list' should not occur")
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        subs = profile.login(False, '1234', 'my-secret', False, self.tenant_id, use_device_code=False,
                             allow_no_subscriptions=False, subscription_finder=finder)

        # assert
        self.assertEqual(self.subscription1_output, subs)

    @mock.patch('azure.identity.DeviceCodeCredential.authenticate', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_login_with_device_code(self, app_mock, authenticate_mock):
        authenticate_mock.return_value = self.authentication_record
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        subs = profile.login(True, None, None, False, None, use_device_code=True,
                             allow_no_subscriptions=False, subscription_finder=finder)

        # assert
        self.assertEqual(self.subscription1_output, subs)

    @mock.patch('azure.identity.DeviceCodeCredential.authenticate', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_login_with_device_code_for_tenant(self, app_mock, authenticate_mock):
        authenticate_mock.return_value = self.authentication_record
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.side_effect = ValueError("'tenants.list' should not occur")
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        subs = profile.login(True, None, None, False, self.tenant_id, use_device_code=True,
                             allow_no_subscriptions=False, subscription_finder=finder)

        # assert
        self.assertEqual(self.subscription1_output, subs)

    def test_login_with_service_principal_secret(self):
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        subs = profile.login(False, 'my app', 'my secret', True, self.tenant_id, use_device_code=True,
                             allow_no_subscriptions=False, subscription_finder=finder)
        output = [{'environmentName': 'AzureCloud',
                   'homeTenantId': 'microsoft.com',
                   'id': '1',
                   'isDefault': True,
                   'managedByTenants': [{'tenantId': '00000003-0000-0000-0000-000000000000'},
                                        {'tenantId': '00000004-0000-0000-0000-000000000000'}],
                   'name': 'foo account',
                   'state': 'Enabled',
                   'tenantId': 'microsoft.com',
                   'user': {
                       'name': 'my app',
                       'type': 'servicePrincipal'}}]
        # assert
        self.assertEqual(output, subs)

    def test_login_with_service_principal_cert(self):
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        subs = profile.login(False, 'my app', test_cert_file, True, self.tenant_id, use_device_code=True,
                             allow_no_subscriptions=False, subscription_finder=finder)
        output = [{'environmentName': 'AzureCloud',
                   'homeTenantId': 'microsoft.com',
                   'id': '1',
                   'isDefault': True,
                   'managedByTenants': [{'tenantId': '00000003-0000-0000-0000-000000000000'},
                                        {'tenantId': '00000004-0000-0000-0000-000000000000'}],
                   'name': 'foo account',
                   'state': 'Enabled',
                   'tenantId': 'microsoft.com',
                   'user': {
                       'name': 'my app',
                       'type': 'servicePrincipal'}}]
        # assert
        self.assertEqual(output, subs)

    @unittest.skip("Not supported by Azure Identity.")
    def test_login_with_service_principal_cert_sn_issuer(self, get_token_mock):
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        subs = profile.login(False, 'my app', test_cert_file, True, self.tenant_id, use_device_code=True,
                             allow_no_subscriptions=False, subscription_finder=finder, use_cert_sn_issuer=True)
        output = [{'environmentName': 'AzureCloud',
                   'homeTenantId': 'microsoft.com',
                   'id': '1',
                   'isDefault': True,
                   'managedByTenants': [{'tenantId': '00000003-0000-0000-0000-000000000000'},
                                        {'tenantId': '00000004-0000-0000-0000-000000000000'}],
                   'name': 'foo account',
                   'state': 'Enabled',
                   'tenantId': 'microsoft.com',
                   'user': {
                       'name': 'my app',
                       'type': 'servicePrincipal',
                       'useCertSNIssuerAuth': True}}]
        # assert
        self.assertEqual(output, subs)

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._get_subscription_client_class', autospec=True)
    @mock.patch.dict('os.environ')
    def test_login_with_environment_credential_service_principal(self, get_client_class_mock):
        os.environ['AZURE_TENANT_ID'] = self.service_principal_tenant_id
        os.environ['AZURE_CLIENT_ID'] = self.service_principal_id
        os.environ['AZURE_CLIENT_SECRET'] = self.service_principal_secret

        client_mock = mock.MagicMock()
        get_client_class_mock.return_value = mock.MagicMock(return_value=client_mock)
        client_mock.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]

        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        subs = profile.login_with_environment_credential()
        output = [{'environmentName': 'AzureCloud',
                   'homeTenantId': 'microsoft.com',
                   'id': '1',
                   'isDefault': True,
                   'managedByTenants': [{'tenantId': '00000003-0000-0000-0000-000000000000'},
                                        {'tenantId': '00000004-0000-0000-0000-000000000000'}],
                   'name': 'foo account',
                   'state': 'Enabled',
                   'tenantId': self.service_principal_tenant_id,
                   'user': {
                       'isEnvironmentCredential': True,
                       'name': self.service_principal_id,
                       'type': 'servicePrincipal'}}]
        # assert
        self.assertEqual(output, subs)

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._get_subscription_client_class', autospec=True)
    @mock.patch('azure.identity.UsernamePasswordCredential.authenticate', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    @mock.patch.dict('os.environ')
    def test_login_with_environment_credential_username_password(self, app_mock, authenticate_mock, get_client_class_mock):
        os.environ['AZURE_USERNAME'] = self.user1
        os.environ['AZURE_PASSWORD'] = "test_user_password"

        authenticate_mock.return_value = self.authentication_record

        arm_client_mock = mock.MagicMock()
        get_client_class_mock.return_value = mock.MagicMock(return_value=arm_client_mock)
        arm_client_mock.tenants.list.return_value = [TenantStub(self.tenant_id)]
        arm_client_mock.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]

        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        subs = profile.login_with_environment_credential()
        output = [{'environmentName': 'AzureCloud',
                   'homeTenantId': 'microsoft.com',
                   'id': '1',
                   'isDefault': True,
                   'managedByTenants': [{'tenantId': '00000003-0000-0000-0000-000000000000'},
                                        {'tenantId': '00000004-0000-0000-0000-000000000000'}],
                   'name': 'foo account',
                   'state': 'Enabled',
                   'tenantId': self.tenant_id,
                   'user': {
                       'isEnvironmentCredential': True,
                       'name': self.user1,
                       'type': 'user'}}]
        # assert
        self.assertEqual(output, subs)

    def test_normalize(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1, [self.subscription1], False)
        expected = self.subscription1_normalized
        self.assertEqual(expected, consolidated[0])
        # verify serialization works
        self.assertIsNotNone(json.dumps(consolidated[0]))

        # Test is_environment is mapped to user.isEnvironmentCredential
        consolidated = profile._normalize_properties(self.user1, [self.subscription1], False, is_environment=True)
        self.assertEqual(consolidated[0]['user']['isEnvironmentCredential'], True)

    def test_normalize_with_unicode_in_subscription_name(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        test_display_name = 'sub' + chr(255)
        polished_display_name = 'sub?'
        test_subscription = SubscriptionStub('subscriptions/sub1',
                                             test_display_name,
                                             SubscriptionState.enabled,
                                             'tenant1')
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1,
                                                     [test_subscription],
                                                     False)
        self.assertTrue(consolidated[0]['name'] in [polished_display_name, test_display_name])

    def test_normalize_with_none_subscription_name(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        test_display_name = None
        polished_display_name = ''
        test_subscription = SubscriptionStub('subscriptions/sub1',
                                             test_display_name,
                                             SubscriptionState.enabled,
                                             'tenant1')
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1,
                                                     [test_subscription],
                                                     False)
        self.assertTrue(consolidated[0]['name'] == polished_display_name)

    def test_update_add_two_different_subscriptions(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        # add the first and verify
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)

        self.assertEqual(len(storage_mock['subscriptions']), 1)
        subscription1 = storage_mock['subscriptions'][0]
        subscription1_is_default = deepcopy(self.subscription1_normalized)
        subscription1_is_default['isDefault'] = True
        self.assertEqual(subscription1, subscription1_is_default)

        # add the second and verify
        consolidated = profile._normalize_properties(self.user2,
                                                     [self.subscription2],
                                                     False)
        profile._set_subscriptions(consolidated)

        self.assertEqual(len(storage_mock['subscriptions']), 2)
        subscription2 = storage_mock['subscriptions'][1]
        subscription2_is_default = deepcopy(self.subscription2_normalized)
        subscription2_is_default['isDefault'] = True
        self.assertEqual(subscription2, subscription2_is_default)

        # verify the old one stays, but no longer active
        self.assertEqual(storage_mock['subscriptions'][0]['name'],
                         subscription1['name'])
        self.assertFalse(storage_mock['subscriptions'][0]['isDefault'])

    def test_update_with_same_subscription_added_twice(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        # add one twice and verify we will have one but with new token
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)

        new_subscription1 = SubscriptionStub(self.id1,
                                             self.display_name1,
                                             self.state1,
                                             self.tenant_id)
        consolidated = profile._normalize_properties(self.user1,
                                                     [new_subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)

        self.assertEqual(len(storage_mock['subscriptions']), 1)
        self.assertTrue(storage_mock['subscriptions'][0]['isDefault'])

    def test_set_active_subscription(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)

        consolidated = profile._normalize_properties(self.user2,
                                                     [self.subscription2],
                                                     False)
        profile._set_subscriptions(consolidated)

        self.assertTrue(storage_mock['subscriptions'][1]['isDefault'])

        profile.set_active_subscription(storage_mock['subscriptions'][0]['id'])
        self.assertFalse(storage_mock['subscriptions'][1]['isDefault'])
        self.assertTrue(storage_mock['subscriptions'][0]['isDefault'])

    def test_default_active_subscription_to_non_disabled_one(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        subscriptions = profile._normalize_properties(
            self.user2, [self.subscription2, self.subscription1], False)

        profile._set_subscriptions(subscriptions)

        # verify we skip the overdued subscription and default to the 2nd one in the list
        self.assertEqual(storage_mock['subscriptions'][1]['name'], self.subscription1.display_name)
        self.assertTrue(storage_mock['subscriptions'][1]['isDefault'])

    def test_get_subscription(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)

        self.assertEqual(self.display_name1, profile.get_subscription()['name'])
        self.assertEqual(self.display_name1,
                         profile.get_subscription(subscription=self.display_name1)['name'])

        sub_id = self.id1.split('/')[-1]
        self.assertEqual(sub_id, profile.get_subscription()['id'])
        self.assertEqual(sub_id, profile.get_subscription(subscription=sub_id)['id'])
        self.assertRaises(CLIError, profile.get_subscription, "random_id")

    def test_get_auth_info_fail_on_user_account(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)

        # testing dump of existing logged in account
        self.assertRaises(CLIError, profile.get_sp_auth_info)

    @mock.patch('azure.cli.core.profiles.get_api_version', autospec=True)
    def test_subscription_finder_constructor(self, get_api_mock):
        cli = DummyCli()
        get_api_mock.return_value = '2016-06-01'
        cli.cloud.endpoints.resource_manager = 'http://foo_arm'
        finder = SubscriptionFinder(cli)
        result = finder._arm_client_factory(mock.MagicMock())
        self.assertEqual(result._client._base_url, 'http://foo_arm')

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_get_auth_info_for_logged_in_service_principal(self, mock_auth_context):
        cli = DummyCli()
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        profile._management_resource_uri = 'https://management.core.windows.net/'
        profile.login(False, '1234', 'my-secret', True, self.tenant_id, use_device_code=False,
                      allow_no_subscriptions=False, subscription_finder=finder)
        # action
        extended_info = profile.get_sp_auth_info()
        # assert
        self.assertEqual(self.id1.split('/')[-1], extended_info['subscriptionId'])
        self.assertEqual('1234', extended_info['clientId'])
        self.assertEqual('my-secret', extended_info['clientSecret'])
        self.assertEqual('https://login.microsoftonline.com', extended_info['activeDirectoryEndpointUrl'])
        self.assertEqual('https://management.azure.com/', extended_info['resourceManagerEndpointUrl'])

    def test_get_auth_info_for_newly_created_service_principal(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1, [self.subscription1], False)
        profile._set_subscriptions(consolidated)
        # action
        extended_info = profile.get_sp_auth_info(name='1234', cert_file='/tmp/123.pem')
        # assert
        self.assertEqual(self.id1.split('/')[-1], extended_info['subscriptionId'])
        self.assertEqual(self.tenant_id, extended_info['tenantId'])
        self.assertEqual('1234', extended_info['clientId'])
        self.assertEqual('/tmp/123.pem', extended_info['clientCertificate'])
        self.assertIsNone(extended_info.get('clientSecret', None))
        self.assertEqual('https://login.microsoftonline.com', extended_info['activeDirectoryEndpointUrl'])
        self.assertEqual('https://management.azure.com/', extended_info['resourceManagerEndpointUrl'])

    def test_create_account_without_subscriptions_thru_service_principal(self):
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = []
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        profile._management_resource_uri = 'https://management.core.windows.net/'

        # action
        result = profile.login(False,
                               '1234',
                               'my-secret',
                               True,
                               self.tenant_id,
                               use_device_code=False,
                               allow_no_subscriptions=True,
                               subscription_finder=finder)
        # assert
        self.assertEqual(1, len(result))
        self.assertEqual(result[0]['id'], self.tenant_id)
        self.assertEqual(result[0]['state'], 'Enabled')
        self.assertEqual(result[0]['tenantId'], self.tenant_id)
        self.assertEqual(result[0]['name'], 'N/A(tenant level account)')
        self.assertTrue(profile.is_tenant_level_account())

    def test_create_account_with_subscriptions_allow_no_subscriptions_thru_service_principal(self):
        """test subscription is returned even with --allow-no-subscriptions. """
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        profile._management_resource_uri = 'https://management.core.windows.net/'

        # action
        result = profile.login(False,
                               '1234',
                               'my-secret',
                               True,
                               self.tenant_id,
                               use_device_code=False,
                               allow_no_subscriptions=True,
                               subscription_finder=finder)
        # assert
        self.assertEqual(1, len(result))
        self.assertEqual(result[0]['id'], self.id1.split('/')[-1])
        self.assertEqual(result[0]['state'], 'Enabled')
        self.assertEqual(result[0]['tenantId'], self.tenant_id)
        self.assertEqual(result[0]['name'], self.display_name1)
        self.assertFalse(profile.is_tenant_level_account())

    @mock.patch('azure.identity.UsernamePasswordCredential.get_token', autospec=True)
    @mock.patch('azure.identity.UsernamePasswordCredential.authenticate', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_create_account_without_subscriptions_thru_common_tenant(self, app_mock, authenticate_mock, get_token_mock):
        get_token_mock.return_value = self.access_token
        authenticate_mock.return_value = self.authentication_record

        cli = DummyCli()
        tenant_object = mock.MagicMock()
        tenant_object.id = "foo-bar"
        tenant_object.tenant_id = self.tenant_id
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = []
        mock_arm_client.tenants.list.return_value = (x for x in [tenant_object])

        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        profile._management_resource_uri = 'https://management.core.windows.net/'

        # action
        result = profile.login(False,
                               '1234',
                               'my-secret',
                               False,
                               None,
                               use_device_code=False,
                               allow_no_subscriptions=True,
                               subscription_finder=finder)

        # assert
        self.assertEqual(1, len(result))
        self.assertEqual(result[0]['id'], self.tenant_id)
        self.assertEqual(result[0]['state'], 'Enabled')
        self.assertEqual(result[0]['tenantId'], self.tenant_id)
        self.assertEqual(result[0]['name'], 'N/A(tenant level account)')

    @mock.patch('azure.cli.core._identity.Identity.login_with_username_password', autospec=True)
    def test_create_account_without_subscriptions_without_tenant(self, login_with_username_password):
        cli = DummyCli()
        from azure.identity import UsernamePasswordCredential
        auth_profile = self.authentication_record
        credential = UsernamePasswordCredential(self.client_id, '1234', 'my-secret')
        login_with_username_password.return_value = [credential, auth_profile]

        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = []
        mock_arm_client.tenants.list.return_value = []
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        # action
        result = profile.login(False,
                               '1234',
                               'my-secret',
                               False,
                               None,
                               use_device_code=False,
                               allow_no_subscriptions=True,
                               subscription_finder=finder)

        # assert
        self.assertTrue(0 == len(result))

    def test_get_current_account_user(self):
        cli = DummyCli()

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        # action
        user = profile.get_current_account_user()

        # verify
        self.assertEqual(user, self.user1)

    @mock.patch('azure.identity.InteractiveBrowserCredential.get_token', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_get_login_credentials(self, app_mock, get_token_mock):
        cli = DummyCli()
        get_token_mock.return_value = TestProfile.raw_token1
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_subscription = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id),
                                             'MSI-DEV-INC', self.state1, '12345678-38d6-4fb2-bad9-b7b93a3e1234')
        consolidated = profile._normalize_properties(self.user1,
                                                     [test_subscription],
                                                     False, None, None)
        profile._set_subscriptions(consolidated)
        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # verify
        self.assertEqual(subscription_id, test_subscription_id)

        # verify the cred.get_token()
        token = cred.get_token()
        self.assertEqual(token, self.raw_token1)

    @mock.patch('azure.cli.core._identity.Identity.migrate_tokens', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_get_login_credentials_with_token_migration(self, app_mock, migrate_tokens_mock):
        # Mimic an old subscription storage without 'useMsalTokenCache'
        adal_storage_mock = {
            'subscriptions': [{
                'id': '12345678-1bf0-4dda-aec3-cb9272f09590',
                'name': 'MSI-DEV-INC',
                'state': 'Enabled',
                'user': {'name': 'foo@foo.com', 'type': 'user'},
                'isDefault': True,
                'tenantId': '12345678-38d6-4fb2-bad9-b7b93a3e1234',
                'environmentName': 'AzureCloud',
                'managedByTenants': []
            }]
        }

        cli = DummyCli()
        profile = Profile(cli_ctx=cli, storage=adal_storage_mock)
        cred, subscription_id, _ = profile.get_login_credentials()
        # make sure migrate_tokens_mock is called
        migrate_tokens_mock.assert_called()

    @mock.patch('azure.identity.InteractiveBrowserCredential.get_token', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_get_login_credentials_aux_subscriptions(self, app_mock, get_token_mock):
        cli = DummyCli()
        get_token_mock.return_value = TestProfile.raw_token1
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_subscription_id2 = '12345678-1bf0-4dda-aec3-cb9272f09591'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_tenant_id2 = '12345678-38d6-4fb2-bad9-b7b93a3e4321'
        test_subscription = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id),
                                             'MSI-DEV-INC', self.state1, test_tenant_id)
        test_subscription2 = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id2),
                                              'MSI-DEV-INC2', self.state1, test_tenant_id2)
        consolidated = profile._normalize_properties(self.user1,
                                                     [test_subscription, test_subscription2],
                                                     False, None, None)
        profile._set_subscriptions(consolidated)
        # action
        cred, subscription_id, _ = profile.get_login_credentials(subscription_id=test_subscription_id,
                                                                 aux_subscriptions=[test_subscription_id2])

        # verify
        self.assertEqual(subscription_id, test_subscription_id)

        # verify the cred._get_token
        token, external_tokens = cred._get_token()
        self.assertEqual(token, self.raw_token1)
        self.assertEqual(external_tokens[0], self.raw_token1)

    @mock.patch('azure.identity.InteractiveBrowserCredential.get_token', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_get_login_credentials_aux_tenants(self, app_mock, get_token_mock):
        cli = DummyCli()
        get_token_mock.return_value = TestProfile.raw_token1
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_subscription_id2 = '12345678-1bf0-4dda-aec3-cb9272f09591'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_tenant_id2 = '12345678-38d6-4fb2-bad9-b7b93a3e4321'
        test_subscription = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id),
                                             'MSI-DEV-INC', self.state1, test_tenant_id)
        test_subscription2 = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id2),
                                              'MSI-DEV-INC2', self.state1, test_tenant_id2)
        consolidated = profile._normalize_properties(self.user1,
                                                     [test_subscription, test_subscription2],
                                                     False, None, None)
        profile._set_subscriptions(consolidated)
        # test only input aux_tenants
        cred, subscription_id, _ = profile.get_login_credentials(subscription_id=test_subscription_id,
                                                                 aux_tenants=[test_tenant_id2])

        # verify
        self.assertEqual(subscription_id, test_subscription_id)

        # verify the cred._get_token
        token, external_tokens = cred._get_token()
        self.assertEqual(token, self.raw_token1)
        self.assertEqual(external_tokens[0], self.raw_token1)

        # test input aux_tenants and aux_subscriptions
        with self.assertRaisesRegexp(CLIError,
                                     "Please specify only one of aux_subscriptions and aux_tenants, not both"):
            cred, subscription_id, _ = profile.get_login_credentials(subscription_id=test_subscription_id,
                                                                     aux_subscriptions=[test_subscription_id2],
                                                                     aux_tenants=[test_tenant_id2])

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    def test_get_login_credentials_msi_system_assigned(self, get_token_mock):
        get_token_mock.return_value = TestProfile.raw_token1

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_user = 'systemAssignedIdentity'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id, 'MSI', self.state1,
                                            test_tenant_id)
        consolidated = profile._normalize_properties(test_user,
                                                     [msi_subscription],
                                                     True)
        profile._set_subscriptions(consolidated)

        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # assert
        self.assertEqual(subscription_id, test_subscription_id)

        token = cred.get_token()
        self.assertEqual(token, self.raw_token1)

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    def test_get_login_credentials_msi_user_assigned_with_client_id(self, get_token_mock):
        get_token_mock.return_value = TestProfile.raw_token1

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_user = 'userAssignedIdentity'
        test_client_id = '12345678-38d6-4fb2-bad9-b7b93a3e8888'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id,
                                            'MSIClient-{}'.format(test_client_id), self.state1, test_tenant_id)
        consolidated = profile._normalize_properties(test_user, [msi_subscription], True)
        profile._set_subscriptions(consolidated, secondary_key_name='name')

        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # assert
        self.assertEqual(subscription_id, test_subscription_id)

        token = cred.get_token()
        self.assertEqual(token, self.raw_token1)

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    def test_get_login_credentials_msi_user_assigned_with_object_id(self, get_token_mock):
        get_token_mock.return_value = TestProfile.raw_token1

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_object_id = '12345678-38d6-4fb2-bad9-b7b93a3e9999'
        msi_subscription = SubscriptionStub('/subscriptions/12345678-1bf0-4dda-aec3-cb9272f09590',
                                            'MSIObject-{}'.format(test_object_id),
                                            self.state1, '12345678-38d6-4fb2-bad9-b7b93a3e1234')
        consolidated = profile._normalize_properties('userAssignedIdentity', [msi_subscription], True)
        profile._set_subscriptions(consolidated, secondary_key_name='name')

        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # assert
        self.assertEqual(subscription_id, test_subscription_id)

        token = cred.get_token()
        self.assertEqual(token, self.raw_token1)

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    def test_get_login_credentials_msi_user_assigned_with_res_id(self, get_token_mock):
        get_token_mock.return_value = self.access_token

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_res_id = ('/subscriptions/{}/resourceGroups/r1/providers/Microsoft.ManagedIdentity/'
                       'userAssignedIdentities/id1').format(test_subscription_id)
        msi_subscription = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id),
                                            'MSIResource-{}'.format(test_res_id),
                                            self.state1, '12345678-38d6-4fb2-bad9-b7b93a3e1234')
        consolidated = profile._normalize_properties('userAssignedIdentity', [msi_subscription], True)
        profile._set_subscriptions(consolidated, secondary_key_name='name')

        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # assert
        self.assertEqual(subscription_id, test_subscription_id)

        token = cred.get_token()
        self.assertEqual(token, self.access_token)

    @mock.patch('azure.identity.InteractiveBrowserCredential.get_token', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_get_raw_token(self, app_mock, get_token_mock):
        cli = DummyCli()
        get_token_mock.return_value = self.access_token

        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False, None, None)
        profile._set_subscriptions(consolidated)

        # action
        # Get token with ADAL-style resource
        resource_result = profile.get_raw_token(resource='https://foo')
        # Get token with MSAL-style scopes
        scopes_result = profile.get_raw_token(scopes=self.msal_scopes)

        # verify
        self.assertEqual(resource_result, scopes_result)
        creds, sub, tenant = scopes_result

        self.assertEqual(creds[0], self.token_entry1['tokenType'])
        self.assertEqual(creds[1], self.raw_token1)
        import datetime
        # the last in the tuple is the whole token entry which has several fields
        self.assertEqual(creds[2]['expiresOn'],
                         datetime.datetime.fromtimestamp(self.access_token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f"))

        # Test get_raw_token with tenant
        creds, sub, tenant = profile.get_raw_token(resource='https://foo', tenant=self.tenant_id)

        self.assertEqual(creds[0], self.token_entry1['tokenType'])
        self.assertEqual(creds[1], self.raw_token1)
        self.assertEqual(creds[2]['expiresOn'],
                         datetime.datetime.fromtimestamp(self.access_token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f"))
        self.assertIsNone(sub)
        self.assertEqual(tenant, self.tenant_id)

    @mock.patch('azure.identity.ClientSecretCredential.get_token', autospec=True)
    @mock.patch('azure.cli.core._identity.MsalSecretStore.retrieve_secret_of_service_principal', autospec=True)
    def test_get_raw_token_for_sp(self, retrieve_secret_of_service_principal, get_token_mock):
        cli = DummyCli()
        retrieve_secret_of_service_principal.return_value = 'fake', 'fake'
        get_token_mock.return_value = self.access_token
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties('sp1',
                                                     [self.subscription1],
                                                     True, None, None)
        profile._set_subscriptions(consolidated)
        # action
        creds, sub, tenant = profile.get_raw_token(resource='https://foo')

        # verify
        self.assertEqual(creds[0], self.token_entry1['tokenType'])
        self.assertEqual(creds[1], self.raw_token1)
        # the last in the tuple is the whole token entry which has several fields
        self.assertEqual(creds[2]['expiresOn'],
                         datetime.datetime.fromtimestamp(self.access_token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f"))
        self.assertEqual(sub, '1')
        self.assertEqual(tenant, self.tenant_id)

        # Test get_raw_token with tenant
        creds, sub, tenant = profile.get_raw_token(resource='https://foo', tenant=self.tenant_id)

        self.assertEqual(creds[0], self.token_entry1['tokenType'])
        self.assertEqual(creds[1], self.raw_token1)
        self.assertEqual(creds[2]['expiresOn'],
                         datetime.datetime.fromtimestamp(self.access_token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f"))
        self.assertIsNone(sub)
        self.assertEqual(tenant, self.tenant_id)

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    def test_get_raw_token_msi_system_assigned(self, get_token_mock):
        get_token_mock.return_value = self.access_token

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_user = 'systemAssignedIdentity'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id,
                                            'MSI', self.state1, test_tenant_id)
        consolidated = profile._normalize_properties(test_user,
                                                     [msi_subscription],
                                                     True)
        profile._set_subscriptions(consolidated)

        # action
        cred, subscription_id, tenant_id = profile.get_raw_token(resource='http://test_resource')

        # assert
        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(cred[0], 'Bearer')
        self.assertEqual(cred[1], self.raw_token1)
        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(tenant_id, test_tenant_id)

        # verify tenant shouldn't be specified for MSI account
        with self.assertRaisesRegexp(CLIError, "MSI"):
            cred, subscription_id, _ = profile.get_raw_token(resource='http://test_resource', tenant=self.tenant_id)

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True, return_value=True)
    @mock.patch('azure.cli.core._profile.in_cloud_console', autospec=True)
    def test_get_raw_token_in_cloud_console(self, mock_in_cloud_console, get_token_mock):
        get_token_mock.return_value = self.access_token

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id,
                                            self.display_name1, self.state1, test_tenant_id)
        consolidated = profile._normalize_properties(self.user1,
                                                     [msi_subscription],
                                                     True)
        consolidated[0]['user']['cloudShellID'] = True
        profile._set_subscriptions(consolidated)

        # action
        cred, subscription_id, tenant_id = profile.get_raw_token(resource='http://test_resource')

        # assert
        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(cred[0], 'Bearer')
        self.assertEqual(cred[1], self.raw_token1)
        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(tenant_id, test_tenant_id)

        # verify tenant shouldn't be specified for Cloud Shell account
        with self.assertRaisesRegexp(CLIError, 'Cloud Shell'):
            cred, subscription_id, _ = profile.get_raw_token(resource='http://test_resource', tenant=self.tenant_id)

    @mock.patch('azure.identity.InteractiveBrowserCredential.get_token', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_get_login_credentials_for_graph_client(self, app_mock, get_token_mock):
        cli = DummyCli()
        get_token_mock.return_value = self.access_token
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1, [self.subscription1],
                                                     False, None, None)
        profile._set_subscriptions(consolidated)
        # action
        cred, _, tenant_id = profile.get_login_credentials(
            resource=cli.cloud.endpoints.active_directory_graph_resource_id)
        _, _ = cred._get_token()
        # verify
        get_token_mock.assert_called_once_with(mock.ANY, 'https://graph.windows.net/.default')
        self.assertEqual(tenant_id, self.tenant_id)

    @mock.patch('azure.identity.InteractiveBrowserCredential.get_token', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_get_login_credentials_for_data_lake_client(self, app_mock, get_token_mock):
        cli = DummyCli()
        get_token_mock.return_value = self.access_token
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1, [self.subscription1],
                                                     False, None, None)
        profile._set_subscriptions(consolidated)
        # action
        cred, _, tenant_id = profile.get_login_credentials(
            resource=cli.cloud.endpoints.active_directory_data_lake_resource_id)
        _, _ = cred._get_token()
        # verify
        get_token_mock.assert_called_once_with(mock.ANY, 'https://datalake.azure.net//.default')
        self.assertEqual(tenant_id, self.tenant_id)

    @mock.patch('msal.PublicClientApplication.remove_account', autospec=True)
    @mock.patch('msal.PublicClientApplication.get_accounts', autospec=True)
    def test_logout(self, mock_get_accounts, mock_remove_account):
        cli = DummyCli()

        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)

        # 1. Log out from CLI, but not from MSAL
        profile._set_subscriptions(consolidated)
        self.assertEqual(1, len(storage_mock['subscriptions']))

        profile.logout(self.user1, clear_credential=False)

        self.assertEqual(0, len(storage_mock['subscriptions']))
        mock_get_accounts.assert_called_with(mock.ANY, self.user1)
        mock_remove_account.assert_not_called()

        # 2. Log out from both CLI and MSAL
        profile._set_subscriptions(consolidated)
        mock_get_accounts.reset_mock()
        mock_remove_account.reset_mock()
        mock_get_accounts.return_value = self.msal_accounts

        profile.logout(self.user1, True)

        self.assertEqual(0, len(storage_mock['subscriptions']))
        mock_get_accounts.assert_called_with(mock.ANY, self.user1)
        mock_remove_account.assert_has_calls([mock.call(mock.ANY, self.msal_accounts[0]),
                                             mock.call(mock.ANY, self.msal_accounts[1])])

        # 3. When already logged out from CLI, log out from MSAL
        profile._set_subscriptions([])
        mock_get_accounts.reset_mock()
        mock_remove_account.reset_mock()
        profile.logout(self.user1, True)
        mock_get_accounts.assert_called_with(mock.ANY, self.user1)
        mock_remove_account.assert_has_calls([mock.call(mock.ANY, self.msal_accounts[0]),
                                              mock.call(mock.ANY, self.msal_accounts[1])])

        # 4. Log out from CLI, when already logged out from MSAL
        profile._set_subscriptions(consolidated)
        mock_get_accounts.reset_mock()
        mock_remove_account.reset_mock()
        mock_get_accounts.return_value = []
        profile.logout(self.user1, True)
        self.assertEqual(0, len(storage_mock['subscriptions']))
        mock_get_accounts.assert_called_with(mock.ANY, self.user1)
        mock_remove_account.assert_not_called()

        # 5. Not logged in to CLI or MSAL
        profile._set_subscriptions([])
        mock_get_accounts.reset_mock()
        mock_remove_account.reset_mock()
        mock_get_accounts.return_value = []
        profile.logout(self.user1, True)
        self.assertEqual(0, len(storage_mock['subscriptions']))
        mock_get_accounts.assert_called_with(mock.ANY, self.user1)
        mock_remove_account.assert_not_called()

    @mock.patch('msal.PublicClientApplication.remove_account', autospec=True)
    @mock.patch('msal.PublicClientApplication.get_accounts', autospec=True)
    def test_logout_all(self, mock_get_accounts, mock_remove_account):
        cli = DummyCli()
        # setup
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        consolidated2 = profile._normalize_properties(self.user2,
                                                      [self.subscription2],
                                                      False)
        # 1. Log out from CLI, but not from MSAL
        profile._set_subscriptions(consolidated + consolidated2)
        self.assertEqual(2, len(storage_mock['subscriptions']))

        profile.logout_all(clear_credential=False)
        self.assertEqual([], storage_mock['subscriptions'])
        mock_get_accounts.assert_called_with(mock.ANY)
        mock_remove_account.assert_not_called()

        # 2. Log out from both CLI and MSAL
        profile._set_subscriptions(consolidated + consolidated2)
        mock_get_accounts.reset_mock()
        mock_remove_account.reset_mock()
        mock_get_accounts.return_value = self.msal_accounts
        profile.logout_all(clear_credential=True)
        self.assertEqual([], storage_mock['subscriptions'])
        mock_get_accounts.assert_called_with(mock.ANY)
        self.assertEqual(mock_remove_account.call_count, 4)

        # 3. When already logged out from CLI, log out from MSAL
        profile._set_subscriptions([])
        mock_get_accounts.reset_mock()
        mock_remove_account.reset_mock()
        mock_get_accounts.return_value = self.msal_accounts
        profile.logout_all(clear_credential=True)
        self.assertEqual([], storage_mock['subscriptions'])
        mock_get_accounts.assert_called_with(mock.ANY)
        self.assertEqual(mock_remove_account.call_count, 4)

        # 4. Log out from CLI, when already logged out from MSAL
        profile._set_subscriptions(consolidated + consolidated2)
        mock_get_accounts.reset_mock()
        mock_remove_account.reset_mock()
        mock_get_accounts.return_value = []
        profile.logout_all(clear_credential=True)
        self.assertEqual([], storage_mock['subscriptions'])
        mock_get_accounts.assert_called_with(mock.ANY)
        mock_remove_account.assert_not_called()

        # 5. Not logged in to CLI or MSAL
        profile._set_subscriptions([])
        mock_get_accounts.reset_mock()
        mock_remove_account.reset_mock()
        mock_get_accounts.return_value = []
        profile.logout_all(clear_credential=True)
        self.assertEqual([], storage_mock['subscriptions'])
        mock_get_accounts.assert_called_with(mock.ANY)
        mock_remove_account.assert_not_called()

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder', autospec=True)
    def test_find_subscriptions_in_cloud_console(self, mock_subscription_finder, get_token_mock):
        class SubscriptionFinderStub:
            def find_using_specific_tenant(self, tenant, credential):
                # make sure the tenant and token args match 'TestProfile.test_msi_access_token'
                if tenant != '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a':
                    raise AssertionError('find_using_specific_tenant was not invoked with expected tenant or token')
                return [TestProfile.subscription1]

        mock_subscription_finder.return_value = SubscriptionFinderStub()

        from azure.core.credentials import AccessToken
        import time
        get_token_mock.return_value = AccessToken(TestProfile.test_msi_access_token,
                                                  int(self.token_entry1['expiresIn'] + time.time()))
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)

        # action
        subscriptions = profile.login_in_cloud_shell()

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'admin3@AzureSDKTeam.onmicrosoft.com')
        self.assertEqual(s['user']['cloudShellID'], True)
        self.assertEqual(s['user']['type'], 'user')
        self.assertEqual(s['name'], self.display_name1)
        self.assertEqual(s['id'], self.id1.split('/')[-1])

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder._get_subscription_client_class', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_system_assigned(self, mock_get_client_class, get_token_mock):
        class SubscriptionFinderStub:
            def find_using_specific_tenant(self, tenant, credential):
                # make sure the tenant and token args match 'TestProfile.test_msi_access_token'
                if tenant != '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a':
                    raise AssertionError('find_using_specific_tenant was not invoked with expected tenant or token')
                return [TestProfile.subscription1]

        mock_subscription_finder.return_value = SubscriptionFinderStub()

        from azure.core.credentials import AccessToken
        import time
        get_token_mock.return_value = AccessToken(TestProfile.test_msi_access_token,
                                                  int(self.token_entry1['expiresIn'] + time.time()))
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False, async_persist=False)

        subscriptions = profile.login_with_managed_identity()

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'systemAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['user']['assignedIdentityInfo'], 'MSI')
        self.assertEqual(s['name'], self.display_name1)
        self.assertEqual(s['id'], self.id1.split('/')[-1])
        self.assertEqual(s['tenantId'], 'microsoft.com')

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder._get_subscription_client_class', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_no_subscriptions(self, mock_get_client_class, get_token_mock):
        class SubscriptionFinderStub:
            def find_using_specific_tenant(self, tenant, credential):
                # make sure the tenant and token args match 'TestProfile.test_msi_access_token'
                if tenant != '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a':
                    raise AssertionError('find_using_specific_tenant was not invoked with expected tenant or token')
                return []

        mock_subscription_finder.return_value = SubscriptionFinderStub()

        from azure.core.credentials import AccessToken
        import time
        get_token_mock.return_value = AccessToken(TestProfile.test_msi_access_token,
                                                  int(self.token_entry1['expiresIn'] + time.time()))
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False, async_persist=False)

        subscriptions = profile.login_with_managed_identity(allow_no_subscriptions=True)

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'systemAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['user']['assignedIdentityInfo'], 'MSI')
        self.assertEqual(s['name'], 'N/A(tenant level account)')
        self.assertEqual(s['id'], self.test_msi_tenant)
        self.assertEqual(s['tenantId'], self.test_msi_tenant)

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder._get_subscription_client_class', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_user_assigned_with_client_id(self, mock_get_client_class, get_token_mock):
        class SubscriptionFinderStub:
            def find_using_specific_tenant(self, tenant, credential):
                # make sure the tenant and token args match 'TestProfile.test_msi_access_token'
                if tenant != '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a':
                    raise AssertionError('find_using_specific_tenant was not invoked with expected tenant or token')
                return [TestProfile.subscription1]

        mock_subscription_finder.return_value = SubscriptionFinderStub()

        from azure.core.credentials import AccessToken
        import time

        get_token_mock.return_value = AccessToken(TestProfile.test_user_msi_access_token,
                                                  int(self.token_entry1['expiresIn'] + time.time()))
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None},
                          use_global_creds_cache=False, async_persist=False)

        test_client_id = '62ac49e6-0438-412c-bdf5-484e7d452936'

        subscriptions = profile.login_with_managed_identity(identity_id=test_client_id)

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'userAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['user']['clientId'], test_client_id)
        self.assertEqual(s['name'], self.display_name1)
        self.assertEqual(s['id'], self.id1.split('/')[-1])
        self.assertEqual(s['tenantId'], 'microsoft.com')

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_user_assigned_with_object_id(self, mock_subscription_finder, get_token_mock):
        class SubscriptionFinderStub:
            def find_using_specific_tenant(self, tenant, credential):
                # make sure the tenant and token args match 'TestProfile.test_msi_access_token'
                if tenant != '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a':
                    raise AssertionError('find_using_specific_tenant was not invoked with expected tenant or token')
                return [TestProfile.subscription1]

        mock_subscription_finder.return_value = SubscriptionFinderStub()

        from azure.core.credentials import AccessToken
        import time

        get_token_mock.return_value = AccessToken(TestProfile.test_user_msi_access_token,
                                                  int(self.token_entry1['expiresIn'] + time.time()))
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None},
                          use_global_creds_cache=False, async_persist=False)

        test_object_id = 'd834c66f-3af8-40b7-b463-ebdce7f3a827'

        subscriptions = profile.login_with_managed_identity(identity_id=test_object_id)

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'userAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['user']['objectId'], test_object_id)
        self.assertEqual(s['name'], self.display_name1)
        self.assertEqual(s['id'], self.id1.split('/')[-1])
        self.assertEqual(s['tenantId'], 'microsoft.com')

    @mock.patch('azure.identity.ManagedIdentityCredential.get_token', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder._get_subscription_client_class', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_user_assigned_with_res_id(self, mock_get_client_class, get_token_mock):
        class SubscriptionFinderStub:
            def find_using_specific_tenant(self, tenant, credential):
                # make sure the tenant and token args match 'TestProfile.test_msi_access_token'
                if tenant != '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a':
                    raise AssertionError('find_using_specific_tenant was not invoked with expected tenant or token')
                return [TestProfile.subscription1]

        mock_subscription_finder.return_value = SubscriptionFinderStub()

        from azure.core.credentials import AccessToken
        import time

        get_token_mock.return_value = AccessToken(TestProfile.test_user_msi_access_token,
                                                  int(self.token_entry1['expiresIn'] + time.time()))
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None},
                          use_global_creds_cache=False, async_persist=False)

        test_resource_id = ('/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourcegroups/qianwens/providers/'
                            'Microsoft.ManagedIdentity/userAssignedIdentities/qianwenidentity')

        subscriptions = profile.login_with_managed_identity(identity_id=test_resource_id)

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'userAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['user']['resourceId'], test_resource_id)
        self.assertEqual(s['name'], self.display_name1)
        self.assertEqual(s['id'], self.id1.split('/')[-1])
        self.assertEqual(s['tenantId'], 'microsoft.com')

    @unittest.skip("todo: wait for identity support")
    @mock.patch('azure.identity.UsernamePasswordCredential.get_token', autospec=True)
    def test_find_subscriptions_thru_username_password_adfs(self, get_token_mock):
        cli = DummyCli()
        TEST_ADFS_AUTH_URL = 'https://adfs.local.azurestack.external/adfs'
        get_token_mock.return_value = self.access_token

        # todo: adfs test should be covered in azure.identity
        def test_acquire_token(self, resource, username, password, client_id):
            global acquire_token_invoked
            acquire_token_invoked = True
            if (self.authority.url == TEST_ADFS_AUTH_URL and self.authority.is_adfs_authority):
                return TestProfile.token_entry1
            else:
                raise ValueError('AuthContext was not initialized correctly for ADFS')

        get_token_mock.return_value = self.access_token
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        cli.cloud.endpoints.active_directory = TEST_ADFS_AUTH_URL
        finder = SubscriptionFinder(cli)
        finder._arm_client_factory = mock_arm_client
        mgmt_resource = 'https://management.core.windows.net/'
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        profile.login(False, '1234', 'my-secret', True, self.tenant_id, use_device_code=False,
                      allow_no_subscriptions=False, subscription_finder=finder)

        # action
        subs = finder.find_from_user_account(self.user1, 'bar', None, mgmt_resource)

        # assert
        self.assertEqual([self.subscription1], subs)

    @mock.patch('azure.identity.UsernamePasswordCredential.get_token', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_refresh_accounts_one_user_account(self, app_mock, get_token_mock):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False, None, None)
        profile._set_subscriptions(consolidated)
        get_token_mock.return_value = self.access_token
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = deepcopy([self.subscription1_raw, self.subscription2_raw])
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)
        # action
        profile.refresh_accounts(finder)

        # assert
        result = storage_mock['subscriptions']
        self.assertEqual(2, len(result))
        self.assertEqual(self.id1.split('/')[-1], result[0]['id'])
        self.assertEqual(self.id2.split('/')[-1], result[1]['id'])
        self.assertTrue(result[0]['isDefault'])

    @mock.patch('azure.identity.UsernamePasswordCredential.get_token', autospec=True)
    @mock.patch('azure.identity.ClientSecretCredential.get_token', autospec=True)
    @mock.patch('azure.cli.core._identity.MsalSecretStore.retrieve_secret_of_service_principal', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_refresh_accounts_one_user_account_one_sp_account(self, app_mock, retrieve_secret_of_service_principal,
                                                              get_token1, get_token2):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        sp_subscription1 = SubscriptionStub('sp-sub/3', 'foo-subname', self.state1, 'foo_tenant.onmicrosoft.com')
        consolidated = profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False, None, None)
        consolidated += profile._normalize_properties('http://foo', [sp_subscription1], True)
        profile._set_subscriptions(consolidated)
        retrieve_secret_of_service_principal.return_value = 'fake', 'fake'
        get_token1.return_value = self.access_token
        get_token2.return_value = self.access_token
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.side_effect = deepcopy(
            [[self.subscription1], [self.subscription2, sp_subscription1]])
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)

        # action
        profile.refresh_accounts(finder)

        # assert
        result = storage_mock['subscriptions']
        self.assertEqual(3, len(result))
        self.assertEqual(self.id1.split('/')[-1], result[0]['id'])
        self.assertEqual(self.id2.split('/')[-1], result[1]['id'])
        self.assertEqual('3', result[2]['id'])
        self.assertTrue(result[0]['isDefault'])

    @mock.patch('azure.identity.UsernamePasswordCredential.get_token', autospec=True)
    @mock.patch('msal.PublicClientApplication', new_callable=PublicClientApplicationMock)
    def test_refresh_accounts_with_nothing(self, app_mock, get_token_mock):
        cli = DummyCli()
        get_token_mock.return_value = self.access_token
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False, None, None)
        profile._set_subscriptions(consolidated)
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = []
        finder = SubscriptionFinder(cli, lambda _: mock_arm_client)
        # action
        profile.refresh_accounts(finder)

        # assert
        result = storage_mock['subscriptions']
        self.assertEqual(0, len(result))

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    def test_credscache_load_tokens_and_sp_creds_with_secret(self, mock_read_file, mock_read_file2, mock_read_file3):
        test_sp = [{
            'servicePrincipalId': 'myapp',
            'servicePrincipalTenant': 'mytenant',
            'accessToken': 'Secret'
        }]
        mock_read_file.return_value = json.dumps(test_sp)
        mock_read_file2.return_value = json.dumps(test_sp)
        mock_read_file3.return_value = json.dumps(test_sp)
        from azure.cli.core._identity import MsalSecretStore
        # action
        creds_cache = MsalSecretStore()
        token, file = creds_cache.retrieve_secret_of_service_principal("myapp", "mytenant")

        self.assertEqual(token, "Secret")

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    def test_credscache_load_tokens_and_sp_creds_with_cert(self, mock_read_file, mock_read_file2, mock_read_file3):
        test_sp = [{
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "certificateFile": 'junkcert.pem'
        }]
        mock_read_file.return_value = json.dumps(test_sp)
        mock_read_file2.return_value = json.dumps(test_sp)
        mock_read_file3.return_value = json.dumps(test_sp)
        from azure.cli.core._identity import MsalSecretStore
        # action
        creds_cache = MsalSecretStore()
        token, file = creds_cache.retrieve_secret_of_service_principal("myapp", "mytenant")

        # assert
        self.assertEqual(file, 'junkcert.pem')

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.save', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.save', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.save', autospec=True)
    def test_credscache_add_new_sp_creds(self, mock_open_for_write1, mock_open_for_write2, mock_open_for_write3,
                                         mock_read_file1, mock_read_file2, mock_read_file3):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        test_sp2 = {
            "servicePrincipalId": "myapp2",
            "servicePrincipalTenant": "mytenant2",
            "accessToken": "Secret2"
        }
        mock_open_for_write1.return_value = None
        mock_open_for_write2.return_value = None
        mock_open_for_write3.return_value = None
        mock_read_file1.return_value = json.dumps([test_sp])
        mock_read_file2.return_value = json.dumps([test_sp])
        mock_read_file3.return_value = json.dumps([test_sp])
        from azure.cli.core._identity import MsalSecretStore
        creds_cache = MsalSecretStore()

        # action
        creds_cache.save_service_principal_cred(test_sp2)

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [test_sp, test_sp2])

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.save', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.save', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.save', autospec=True)
    def test_credscache_add_preexisting_sp_creds(self, mock_open_for_write1, mock_open_for_write2, mock_open_for_write3,
                                                 mock_read_file1, mock_read_file2, mock_read_file3):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write1.return_value = None
        mock_open_for_write2.return_value = None
        mock_open_for_write3.return_value = None
        mock_read_file1.return_value = json.dumps([test_sp])
        mock_read_file2.return_value = json.dumps([test_sp])
        mock_read_file3.return_value = json.dumps([test_sp])
        from azure.cli.core._identity import MsalSecretStore
        creds_cache = MsalSecretStore()

        # action
        creds_cache.save_service_principal_cred(test_sp)

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [test_sp])

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.save', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.save', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.save', autospec=True)
    def test_credscache_add_preexisting_sp_new_secret(self, mock_open_for_write1, mock_open_for_write2,
                                                      mock_open_for_write3, mock_read_file1,
                                                      mock_read_file2, mock_read_file3):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write1.return_value = None
        mock_open_for_write2.return_value = None
        mock_open_for_write3.return_value = None
        mock_read_file1.return_value = json.dumps([test_sp])
        mock_read_file2.return_value = json.dumps([test_sp])
        mock_read_file3.return_value = json.dumps([test_sp])
        from azure.cli.core._identity import MsalSecretStore
        creds_cache = MsalSecretStore()
        new_creds = test_sp.copy()
        new_creds['accessToken'] = 'Secret2'
        # action
        creds_cache.save_service_principal_cred(new_creds)

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [new_creds])

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.save', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.save', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.save', autospec=True)
    def test_credscache_remove_creds(self, mock_open_for_write1, mock_open_for_write2, mock_open_for_write3,
                                     mock_read_file1, mock_read_file2, mock_read_file3):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write1.return_value = None
        mock_open_for_write2.return_value = None
        mock_open_for_write3.return_value = None
        mock_read_file1.return_value = json.dumps([test_sp])
        mock_read_file2.return_value = json.dumps([test_sp])
        mock_read_file3.return_value = json.dumps([test_sp])
        from azure.cli.core._identity import MsalSecretStore
        creds_cache = MsalSecretStore()

        # action logout a service principal
        creds_cache.remove_cached_creds('myapp')

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [])

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    def test_credscache_good_error_on_file_corruption(self, mock_read_file1, mock_read_file2, mock_read_file3):
        mock_read_file1.side_effect = ValueError('a bad error for you')
        mock_read_file2.side_effect = ValueError('a bad error for you')
        mock_read_file3.side_effect = ValueError('a bad error for you')

        from azure.cli.core._identity import MsalSecretStore
        creds_cache = MsalSecretStore()

        # assert
        with self.assertRaises(CLIError) as context:
            creds_cache._load_cached_creds()

        self.assertTrue(re.findall(r'bad error for you', str(context.exception)))

    def test_service_principal_auth_client_secret(self):
        from azure.cli.core._identity import ServicePrincipalAuth
        sp_auth = ServicePrincipalAuth('sp_id1', 'tenant1', 'verySecret!')
        result = sp_auth.get_entry_to_persist()
        self.assertEqual(result, {
            'servicePrincipalId': 'sp_id1',
            'servicePrincipalTenant': 'tenant1',
            'accessToken': 'verySecret!'
        })

    def test_service_principal_auth_client_cert(self):
        from azure.cli.core._identity import ServicePrincipalAuth
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')
        sp_auth = ServicePrincipalAuth('sp_id1', 'tenant1', None, test_cert_file)

        result = sp_auth.get_entry_to_persist()
        self.assertEqual(result, {
            'servicePrincipalId': 'sp_id1',
            'servicePrincipalTenant': 'tenant1',
            'certificateFile': test_cert_file,
            'thumbprint': 'F0:6A:53:84:8B:BE:71:4A:42:90:D6:9D:33:52:79:C1:D0:10:73:FD'
        })

    def test_service_principal_auth_client_cert_err(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'err_sp_cert.pem')
        with self.assertRaisesRegexp(CLIError, 'Invalid certificate'):
            ServicePrincipalAuth(test_cert_file)

    @unittest.skip("todo: wait for identity support")
    @mock.patch('adal.AuthenticationContext', autospec=True)
    @mock.patch('azure.cli.core._profile._get_authorization_code', autospec=True)
    def test_find_using_common_tenant_mfa_warning(self, _get_authorization_code_mock, mock_auth_context):
        # Assume 2 tenants. Home tenant tenant1 doesn't require MFA, but tenant2 does
        # todo: @jiashuo
        import adal
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        tenant2_mfa_id = 'tenant2-0000-0000-0000-000000000000'
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id), TenantStub(tenant2_mfa_id)]
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        token_cache = adal.TokenCache()
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, token_cache, lambda _: mock_arm_client)

        adal_error_mfa = adal.AdalError(error_msg="", error_response={
            'error': 'interaction_required',
            'error_description': "AADSTS50076: Due to a configuration change made by your administrator, "
                                 "or because you moved to a new location, you must use multi-factor "
                                 "authentication to access '797f4846-ba00-4fd7-ba43-dac1f8f63013'.\n"
                                 "Trace ID: 00000000-0000-0000-0000-000000000000\n"
                                 "Correlation ID: 00000000-0000-0000-0000-000000000000\n"
                                 "Timestamp: 2020-03-10 04:42:59Z",
            'error_codes': [50076],
            'timestamp': '2020-03-10 04:42:59Z',
            'trace_id': '00000000-0000-0000-0000-000000000000',
            'correlation_id': '00000000-0000-0000-0000-000000000000',
            'error_uri': 'https://login.microsoftonline.com/error?code=50076',
            'suberror': 'basic_action'})

        # adal_error_mfa are raised on the second call
        mock_auth_context.acquire_token.side_effect = [self.token_entry1, adal_error_mfa]

        # action
        all_subscriptions = finder.find_using_common_tenant(access_token="token1",
                                                            resource='https://management.core.windows.net/')

        # assert
        # subscriptions are correctly returned
        self.assertEqual(all_subscriptions, [self.subscription1])
        self.assertEqual(mock_auth_context.acquire_token.call_count, 2)

        # With pytest, use -o log_cli=True to manually check the log

class FileHandleStub(object):  # pylint: disable=too-few-public-methods

    def write(self, content):
        pass

    def __enter__(self):
        return self

    def __exit__(self, _2, _3, _4):
        pass


class SubscriptionStub(Subscription):  # pylint: disable=too-few-public-methods

    def __init__(self, id, display_name, state, tenant_id, managed_by_tenants=[], home_tenant_id=None):  # pylint: disable=redefined-builtin
        policies = SubscriptionPolicies()
        policies.spending_limit = SpendingLimit.current_period_off
        policies.quota_id = 'some quota'
        super(SubscriptionStub, self).__init__(subscription_policies=policies,
                                               authorization_source='some_authorization_source')
        self.id = id
        self.subscription_id = id.split('/')[1]
        self.display_name = display_name
        self.state = state
        # for a SDK Subscription, tenant_id means home tenant id
        # for a _find_using_specific_tenant Subscription, tenant_id means token tenant id
        self.tenant_id = tenant_id
        self.managed_by_tenants = managed_by_tenants
        # if home_tenant_id is None, this denotes a Subscription from SDK
        if home_tenant_id:
            self.home_tenant_id = home_tenant_id


class ManagedByTenantStub(ManagedByTenant):  # pylint: disable=too-few-public-methods

    def __init__(self, tenant_id):  # pylint: disable=redefined-builtin
        self.tenant_id = tenant_id


class TenantStub(object):  # pylint: disable=too-few-public-methods

    def __init__(self, tenant_id, display_name="DISPLAY_NAME"):
        self.tenant_id = tenant_id
        self.display_name = display_name
        self.additional_properties = {'displayName': display_name}


class MSRestAzureAuthStub:
    def __init__(self, *args, **kwargs):
        self._token = {
            'token_type': 'Bearer',
            'access_token': TestProfile.test_msi_access_token
        }
        self.set_token_invoked_count = 0
        self.token_read_count = 0
        self.client_id = kwargs.get('client_id')
        self.object_id = kwargs.get('object_id')
        self.msi_res_id = kwargs.get('msi_res_id')

    def set_token(self):
        self.set_token_invoked_count += 1

    @property
    def token(self):
        self.token_read_count += 1
        return self._token

    @token.setter
    def token(self, value):
        self._token = value


class TestProfileUtils(unittest.TestCase):
    def test_get_authority_and_tenant(self):
        from azure.cli.core._profile import _detect_adfs_authority

        # Public cloud, without tenant
        expected_authority = "https://login.microsoftonline.com"
        self.assertEqual(_detect_adfs_authority("https://login.microsoftonline.com", None),
                         (expected_authority, None))
        # Public cloud, with tenant
        self.assertEqual(_detect_adfs_authority("https://login.microsoftonline.com", '00000000-0000-0000-0000-000000000001'),
                         (expected_authority, '00000000-0000-0000-0000-000000000001'))

        # ADFS, without tenant
        expected_authority = "https://adfs.redmond.azurestack.corp.microsoft.com"
        self.assertEqual(_detect_adfs_authority("https://adfs.redmond.azurestack.corp.microsoft.com/adfs", None),
                         (expected_authority, 'adfs'))
        # ADFS, without tenant (including a trailing /)
        self.assertEqual(_detect_adfs_authority("https://adfs.redmond.azurestack.corp.microsoft.com/adfs/", None),
                         (expected_authority, 'adfs'))
        # ADFS, with tenant
        self.assertEqual(_detect_adfs_authority("https://adfs.redmond.azurestack.corp.microsoft.com/adfs", '00000000-0000-0000-0000-000000000001'),
                         (expected_authority, 'adfs'))


class TestUtils(unittest.TestCase):
    def test_get_authority_and_tenant(self):
        # Public cloud
        # Default tenant
        self.assertEqual(_detect_adfs_authority('https://login.microsoftonline.com', None),
                         ('https://login.microsoftonline.com', None))
        # Trailing slash is stripped
        self.assertEqual(_detect_adfs_authority('https://login.microsoftonline.com/', None),
                         ('https://login.microsoftonline.com', None))
        # Custom tenant
        self.assertEqual(_detect_adfs_authority('https://login.microsoftonline.com', '601d729d-0000-0000-0000-000000000000'),
                         ('https://login.microsoftonline.com', '601d729d-0000-0000-0000-000000000000'))

        # ADFS
        # Default tenant
        self.assertEqual(_detect_adfs_authority('https://adfs.redmond.azurestack.corp.microsoft.com/adfs', None),
                         ('https://adfs.redmond.azurestack.corp.microsoft.com', 'adfs'))
        # Trailing slash is stripped
        self.assertEqual(_detect_adfs_authority('https://adfs.redmond.azurestack.corp.microsoft.com/adfs/', None),
                         ('https://adfs.redmond.azurestack.corp.microsoft.com', 'adfs'))
        # Tenant ID is discarded
        self.assertEqual(_detect_adfs_authority('https://adfs.redmond.azurestack.corp.microsoft.com/adfs', '601d729d-0000-0000-0000-000000000000'),
                         ('https://adfs.redmond.azurestack.corp.microsoft.com', 'adfs'))


if __name__ == '__main__':
    unittest.main()
