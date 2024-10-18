# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
import json
import datetime
import unittest
from copy import deepcopy
from unittest import mock

from azure.cli.core._profile import (Profile, SubscriptionFinder, _attach_token_tenant,
                                     _transform_subscription_for_multiapi)
from azure.cli.core.auth.util import AccessToken
from azure.cli.core.mock import DummyCli
from azure.mgmt.resource.subscriptions.models import \
    (Subscription, SubscriptionPolicies, SpendingLimit, ManagedByTenant)

from knack.util import CLIError

MOCK_ACCESS_TOKEN = "mock_access_token"
MOCK_EXPIRES_ON_STR = "1630920323"
MOCK_EXPIRES_ON_INT = 1630920323
MOCK_EXPIRES_ON_DATETIME = datetime.datetime.fromtimestamp(MOCK_EXPIRES_ON_INT).strftime("%Y-%m-%d %H:%M:%S.%f")
BEARER = 'Bearer'

MOCK_TENANT_DISPLAY_NAME = 'TEST_TENANT_DISPLAY_NAME'
MOCK_TENANT_DEFAULT_DOMAIN = 'test.onmicrosoft.com'


class CredentialMock:

    def __init__(self, *args, **kwargs):
        # If get_token_scopes is checked, make sure to create a new instance of CredentialMock
        # to avoid interference from other tests.
        self.get_token_scopes = None
        super().__init__()

    def get_token(self, *scopes, **kwargs):
        self.get_token_scopes = scopes
        return AccessToken(MOCK_ACCESS_TOKEN, MOCK_EXPIRES_ON_INT)


# Used as the return_value of azure.cli.core.auth.identity.Identity.get_user_credential
# If we directly patch azure.cli.core.auth.msal_authentication.UserCredential with CredentialMock,
# get_user_credential will prepare MSAL token cache and HTTP cache which is time-consuming and unnecessary.
credential_mock = CredentialMock()


class MSRestAzureAuthStub:

    def __init__(self, *args, **kwargs):
        self._token = {
            'token_type': 'Bearer',
            'access_token': TestProfile.test_msi_access_token,
            'expires_on': MOCK_EXPIRES_ON_STR
        }
        self.set_token_invoked_count = 0
        self.token_read_count = 0
        self.get_token_scopes = None
        self.client_id = kwargs.get('client_id')
        self.object_id = kwargs.get('object_id')
        self.msi_res_id = kwargs.get('msi_res_id')
        self.resource = kwargs.get('resource')

    def set_token(self):
        self.set_token_invoked_count += 1

    @property
    def token(self):
        self.token_read_count += 1
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    def get_token(self, *args, **kwargs):
        self.get_token_scopes = args
        return AccessToken(self.token['access_token'], int(self.token['expires_on']))


class TestProfile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tenant_id = 'microsoft.com'
        cls.tenant_display_name = MOCK_TENANT_DISPLAY_NAME
        cls.tenant_default_domain = MOCK_TENANT_DEFAULT_DOMAIN

        cls.user1 = 'foo@foo.com'
        cls.user_identity_mock = {
            'username': cls.user1,
            'tenantId': cls.tenant_id
        }

        cls.id1 = 'subscriptions/1'
        cls.display_name1 = 'foo account'
        cls.home_account_id = "00000003-0000-0000-0000-000000000000.00000003-0000-0000-0000-000000000000"
        cls.client_id = "00000003-0000-0000-0000-000000000000"
        cls.state1 = 'Enabled'
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

        cls.subscription1_with_tenant_info_output = [{
            'environmentName': 'AzureCloud',
            'homeTenantId': 'microsoft.com',
            'id': '1',
            'isDefault': True,
            'managedByTenants': [{'tenantId': '00000003-0000-0000-0000-000000000000'},
                                 {'tenantId': '00000004-0000-0000-0000-000000000000'}],
            'name': 'foo account',
            'state': 'Enabled',
            'tenantId': 'microsoft.com',
            'tenantDisplayName': MOCK_TENANT_DISPLAY_NAME,
            'tenantDefaultDomain': MOCK_TENANT_DEFAULT_DOMAIN,
            'user': {
                'name': 'foo@foo.com',
                'type': 'user'
            }}]

        # Dummy result of azure.cli.core._profile.SubscriptionFinder.find_using_specific_tenant
        # It has home_tenant_id which is mapped from tenant_id. tenant_id now denotes token tenant.
        cls.subscription1 = SubscriptionStub(cls.id1,
                                             cls.display_name1,
                                             cls.state1,
                                             tenant_id=cls.tenant_id,
                                             managed_by_tenants=cls.managed_by_tenants,
                                             home_tenant_id=cls.tenant_id)

        # Dummy result of azure.cli.core._profile.SubscriptionFinder.find_using_common_tenant
        # It also contains tenant information, compared to the result of find_using_specific_tenant
        cls.subscription1_with_tenant_info = SubscriptionStub(
            cls.id1, cls.display_name1, cls.state1,
            tenant_id=cls.tenant_id, managed_by_tenants=cls.managed_by_tenants,
            home_tenant_id=cls.tenant_id,
            tenant_display_name=cls.tenant_display_name, tenant_default_domain=cls.tenant_default_domain)

        # Dummy result of azure.cli.core._profile.Profile._normalize_properties
        cls.subscription1_normalized = {
            'environmentName': 'AzureCloud',
            'id': '1',
            'name': cls.display_name1,
            'state': cls.state1,
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
        import time
        cls.access_token = AccessToken(cls.raw_token1, int(cls.token_entry1['expiresIn'] + time.time()))
        cls.user2 = 'bar@bar.com'
        cls.id2 = 'subscriptions/2'
        cls.display_name2 = 'bar account'
        cls.state2 = 'PastDue'
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
            'state': cls.state2,
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

        cls.adal_resource = 'https://foo/'
        cls.msal_scopes = ['https://foo//.default']

        cls.service_principal_id = "00000001-0000-0000-0000-000000000000"
        cls.service_principal_secret = "test_secret"
        cls.service_principal_tenant_id = "00000001-0000-0000-0000-000000000000"

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.login_with_auth_code', autospec=True)
    @mock.patch('azure.cli.core._profile.can_launch_browser', autospec=True, return_value=True)
    def test_login_with_auth_code(self, can_launch_browser_mock, login_with_auth_code_mock, get_user_credential_mock,
                                  create_subscription_client_mock):
        login_with_auth_code_mock.return_value = self.user_identity_mock

        cli = DummyCli()
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        subs = profile.login(True, None, None, False, None, use_device_code=False, allow_no_subscriptions=False)

        # assert
        login_with_auth_code_mock.assert_called_once()
        get_user_credential_mock.assert_called()
        self.assertEqual(self.subscription1_with_tenant_info_output, subs)

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.login_with_device_code', autospec=True)
    def test_login_with_device_code(self, login_with_device_code_mock, get_user_credential_mock,
                                    create_subscription_client_mock):
        login_with_device_code_mock.return_value = self.user_identity_mock

        cli = DummyCli()
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        subs = profile.login(True, None, None, False, None, use_device_code=True, allow_no_subscriptions=False)

        # assert
        login_with_device_code_mock.assert_called_once()
        self.assertEqual(self.subscription1_with_tenant_info_output, subs)

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.login_with_device_code', autospec=True)
    @mock.patch('azure.cli.core._profile.can_launch_browser', autospec=True, return_value=False)
    def test_login_fallback_to_device_code_no_browser(self, can_launch_browser_mock, login_with_device_code_mock,
                                                      get_user_credential_mock, create_subscription_client_mock):
        login_with_device_code_mock.return_value = self.user_identity_mock

        cli = DummyCli()
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        subs = profile.login(True, None, None, False, None, use_device_code=True, allow_no_subscriptions=False)

        # assert
        login_with_device_code_mock.assert_called_once()
        self.assertEqual(self.subscription1_with_tenant_info_output, subs)

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.login_with_device_code', autospec=True)
    @mock.patch('azure.cli.core._profile.is_github_codespaces', autospec=True, return_value=True)
    @mock.patch('azure.cli.core._profile.can_launch_browser', autospec=True, return_value=True)
    def test_login_fallback_to_device_code_github_codespaces(self, can_launch_browser_mock, is_github_codespaces_mock,
                                                             login_with_device_code_mock, get_user_credential_mock,
                                                             create_subscription_client_mock):
        # GitHub Codespaces does support launching a browser (actually a new tab),
        # so we mock can_launch_browser to True.
        login_with_device_code_mock.return_value = self.user_identity_mock

        cli = DummyCli()
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        subs = profile.login(True, None, None, False, None, use_device_code=True, allow_no_subscriptions=False)

        # assert
        login_with_device_code_mock.assert_called_once()
        self.assertEqual(self.subscription1_with_tenant_info_output, subs)

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.login_with_device_code', autospec=True)
    def test_login_with_device_code_for_tenant(self, login_with_device_code_mock, get_user_credential_mock,
                                               create_subscription_client_mock):
        login_with_device_code_mock.return_value = self.user_identity_mock

        cli = DummyCli()
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        subs = profile.login(True, None, None, False, self.tenant_id, use_device_code=True,
                             allow_no_subscriptions=False)

        # assert
        self.assertEqual(self.subscription1_output, subs)

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.login_with_username_password', autospec=True)
    def test_login_with_username_password_for_tenant(self, login_with_username_password_mock, get_user_credential_mock,
                                                     create_subscription_client_mock):
        login_with_username_password_mock.return_value = self.user_identity_mock

        cli = DummyCli()
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        subs = profile.login(False, '1234', 'my-secret', False, self.tenant_id, use_device_code=False,
                             allow_no_subscriptions=False)

        self.assertEqual(self.subscription1_output, subs)

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_service_principal_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.login_with_service_principal', autospec=True)
    def test_login_with_service_principal(self, login_with_service_principal_mock,
                                          get_service_principal_credential_mock,
                                          create_subscription_client_mock):
        cli = DummyCli()
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        subs = profile.login(False, 'my app', {'secret': 'very_secret'}, True, self.tenant_id, use_device_code=True,
                             allow_no_subscriptions=False)
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

        login_with_service_principal_mock.assert_called_with(mock.ANY, 'my app', {'secret': 'very_secret'},
                                                             ['https://management.core.windows.net//.default'])
        self.assertEqual(output, subs)

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    def test_login_in_cloud_shell(self, msi_auth_mock, create_subscription_client_mock):
        msi_auth_mock.return_value = MSRestAzureAuthStub()

        cli = DummyCli()
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        profile = Profile(cli_ctx=cli, storage={'subscriptions': None})

        subscriptions = profile.login_in_cloud_shell()

        # Check correct token is used
        assert create_subscription_client_mock.call_args[0][1].token['access_token'] == TestProfile.test_msi_access_token

        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'admin3@AzureSDKTeam.onmicrosoft.com')
        self.assertEqual(s['tenantId'], '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a')
        self.assertEqual(s['user']['cloudShellID'], True)
        self.assertEqual(s['user']['type'], 'user')
        self.assertEqual(s['name'], self.display_name1)
        self.assertEqual(s['id'], self.id1.split('/')[-1])

    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_system_assigned(self, create_subscription_client_mock, mock_get):
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)

        test_token_entry = {
            'token_type': 'Bearer',
            'access_token': TestProfile.test_msi_access_token
        }
        encoded_test_token = json.dumps(test_token_entry).encode()
        good_response = mock.MagicMock()
        good_response.status_code = 200
        good_response.content = encoded_test_token
        mock_get.return_value = good_response

        subscriptions = profile.login_with_managed_identity()

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'systemAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['user']['assignedIdentityInfo'], 'MSI')
        self.assertEqual(s['name'], self.display_name1)
        self.assertEqual(s['id'], self.id1.split('/')[-1])
        self.assertEqual(s['tenantId'], '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a')

    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_no_subscriptions(self, create_subscription_client_mock, mock_get):
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.subscriptions.list.return_value = []
        create_subscription_client_mock.return_value = mock_subscription_client

        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)

        test_token_entry = {
            'token_type': 'Bearer',
            'access_token': TestProfile.test_msi_access_token
        }
        encoded_test_token = json.dumps(test_token_entry).encode()
        good_response = mock.MagicMock()
        good_response.status_code = 200
        good_response.content = encoded_test_token
        mock_get.return_value = good_response

        subscriptions = profile.login_with_managed_identity(allow_no_subscriptions=True)

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]

        self.assertEqual(s['name'], 'N/A(tenant level account)')
        self.assertEqual(s['id'], self.test_msi_tenant)
        self.assertEqual(s['tenantId'], self.test_msi_tenant)

        self.assertEqual(s['user']['name'], 'systemAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['user']['assignedIdentityInfo'], 'MSI')

    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_user_assigned_with_client_id(self, create_subscription_client_mock, mock_get):
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)

        test_token_entry = {
            'token_type': 'Bearer',
            'access_token': TestProfile.test_msi_access_token
        }
        test_client_id = '54826b22-38d6-4fb2-bad9-b7b93a3e9999'
        encoded_test_token = json.dumps(test_token_entry).encode()
        good_response = mock.MagicMock()
        good_response.status_code = 200
        good_response.content = encoded_test_token
        mock_get.return_value = good_response

        subscriptions = profile.login_with_managed_identity(identity_id=test_client_id)

        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['name'], self.display_name1)
        self.assertEqual(s['id'], self.id1.split('/')[-1])
        self.assertEqual(s['tenantId'], '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a')

        self.assertEqual(s['user']['name'], 'userAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['user']['assignedIdentityInfo'], 'MSIClient-{}'.format(test_client_id))

    @mock.patch('azure.cli.core.auth.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_user_assigned_with_object_id(self, create_subscription_client_mock,
                                                                            mock_msi_auth):
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        from azure.cli.core.azclierror import AzureResponseError
        class AuthStub:
            def __init__(self, **kwargs):
                self.token = None
                self.client_id = kwargs.get('client_id')
                self.object_id = kwargs.get('object_id')
                # since msrestazure 0.4.34, set_token in init
                self.set_token()

            def set_token(self):
                # here we will reject the 1st sniffing of trying with client_id and then acccept the 2nd
                if self.object_id:
                    self.token = {
                        'token_type': 'Bearer',
                        'access_token': TestProfile.test_msi_access_token
                    }
                else:
                    raise AzureResponseError('Failed to connect to MSI. Please make sure MSI is configured correctly.\n'
                                             'Get Token request returned http error: 400, reason: Bad Request')

        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None})

        mock_msi_auth.side_effect = AuthStub
        test_object_id = '54826b22-38d6-4fb2-bad9-b7b93a3e9999'

        subscriptions = profile.login_with_managed_identity(identity_id=test_object_id)

        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'userAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['user']['assignedIdentityInfo'], 'MSIObject-{}'.format(test_object_id))

    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_user_assigned_with_res_id(self, create_subscription_client_mock,
                                                                         mock_get):

        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)

        test_token_entry = {
            'token_type': 'Bearer',
            'access_token': TestProfile.test_msi_access_token
        }
        test_res_id = ('/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourcegroups/g1/'
                       'providers/Microsoft.ManagedIdentity/userAssignedIdentities/id1')

        encoded_test_token = json.dumps(test_token_entry).encode()
        good_response = mock.MagicMock()
        good_response.status_code = 200
        good_response.content = encoded_test_token
        mock_get.return_value = good_response

        subscriptions = profile.login_with_managed_identity(identity_id=test_res_id)

        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'userAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(subscriptions[0]['user']['assignedIdentityInfo'], 'MSIResource-{}'.format(test_res_id))

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.login_with_auth_code', autospec=True)
    @mock.patch('azure.cli.core._profile.can_launch_browser', autospec=True, return_value=True)
    def test_login_no_subscription(self, can_launch_browser_mock,
                                   login_with_auth_code_mock, get_user_credential_mock,
                                   create_subscription_client_mock):
        login_with_auth_code_mock.return_value = self.user_identity_mock

        cli = DummyCli()
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_subscription_client.subscriptions.list.return_value = []
        create_subscription_client_mock.return_value = mock_subscription_client

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        subs = profile.login(True, None, None, False, None, use_device_code=False, allow_no_subscriptions=True)

        self.assertEqual(1, len(subs))
        self.assertEqual(subs[0]['id'], self.tenant_id)
        self.assertEqual(subs[0]['state'], 'Enabled')
        self.assertEqual(subs[0]['tenantId'], self.tenant_id)
        self.assertEqual(subs[0]['name'], 'N/A(tenant level account)')
        self.assertTrue(profile.is_tenant_level_account())

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.login_with_auth_code', autospec=True)
    @mock.patch('azure.cli.core._profile.can_launch_browser', autospec=True, return_value=True)
    def test_login_no_tenant(self, can_launch_browser_mock,
                             login_with_auth_code_mock, get_user_credential_mock,
                             create_subscription_client_mock):
        login_with_auth_code_mock.return_value = self.user_identity_mock

        cli = DummyCli()
        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = []
        mock_subscription_client.subscriptions.list.return_value = []
        create_subscription_client_mock.return_value = mock_subscription_client

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        subs = profile.login(True, None, None, False, None, use_device_code=False, allow_no_subscriptions=True)

        assert subs == []

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.login_with_auth_code', autospec=True)
    @mock.patch('azure.cli.core._profile.can_launch_browser', autospec=True, return_value=True)
    def test_login_with_auth_code_adfs(self, can_launch_browser_mock,
                                       login_with_auth_code_mock, get_user_credential_mock,
                                       create_subscription_client_mock):
        cli = DummyCli()
        TEST_ADFS_AUTH_URL = 'https://adfs.local.azurestack.external/adfs'

        def login_with_auth_code_mock_side_effect(identity_self, *args, **kwargs):
            assert identity_self.authority == TEST_ADFS_AUTH_URL
            assert identity_self._is_adfs
            return self.user_identity_mock

        login_with_auth_code_mock.side_effect = login_with_auth_code_mock_side_effect

        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]

        mock_subscription_client = mock.MagicMock()
        mock_subscription_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_subscription_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_subscription_client

        cli.cloud.endpoints.active_directory = TEST_ADFS_AUTH_URL

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        subs = profile.login(True, None, None, False, None)

        self.assertEqual(self.subscription1_with_tenant_info_output, subs)

    def test_normalize(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        consolidated = profile._normalize_properties(self.user1, [self.subscription1], False)
        expected = self.subscription1_normalized
        self.assertEqual(expected, consolidated[0])
        # verify serialization works
        self.assertIsNotNone(json.dumps(consolidated[0]))

    def test_normalize_v2016_06_01(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        from azure.mgmt.resource.subscriptions.v2016_06_01.models import Subscription \
            as Subscription_v2016_06_01
        subscription = Subscription_v2016_06_01()
        subscription.id = self.id1
        subscription.display_name = self.display_name1
        subscription.state = self.state1
        subscription.tenant_id = self.tenant_id

        consolidated = profile._normalize_properties(self.user1, [subscription], False)

        # The subscription shouldn't have managed_by_tenants and home_tenant_id
        expected = {
            'id': '1',
            'name': self.display_name1,
            'state': 'Enabled',
            'user': {
                'name': 'foo@foo.com',
                'type': 'user'
            },
            'isDefault': False,
            'tenantId': self.tenant_id,
            'environmentName': 'AzureCloud'
        }
        self.assertEqual(expected, consolidated[0])
        # verify serialization works
        self.assertIsNotNone(json.dumps(consolidated[0]))

    def test_update_add_two_different_subscriptions(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)

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
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)

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
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)

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
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)

        subscriptions = profile._normalize_properties(
            self.user2, [self.subscription2, self.subscription1], False)

        profile._set_subscriptions(subscriptions)

        # verify we skip the overdued subscription and default to the 2nd one in the list
        self.assertEqual(storage_mock['subscriptions'][1]['name'], self.subscription1.display_name)
        self.assertTrue(storage_mock['subscriptions'][1]['isDefault'])

    def test_get_subscription(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)

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

    @mock.patch('azure.cli.core.profiles.get_api_version', autospec=True)
    def test_subscription_finder_constructor(self, get_api_mock):
        cli = DummyCli()
        get_api_mock.return_value = '2019-11-01'
        cli.cloud.endpoints.resource_manager = 'http://foo_arm'
        finder = SubscriptionFinder(cli)
        result = finder._create_subscription_client(mock.MagicMock())
        self.assertEqual(result._client._base_url, 'http://foo_arm')

    def test_get_current_account_user(self):
        try:
            active_account = self.get_subscription()
        except CLIError:
            raise CLIError('There are no active accounts.')

        return active_account[_USER_ENTITY][_USER_NAME]

    def test_get_login_credentials(self, resource=None, client_id=None, subscription_id=None, aux_subscriptions=None,
                              aux_tenants=None):
        """Get a CredentialAdaptor instance to be used with both Track 1 and Track 2 SDKs.

        :param resource: The resource ID to acquire an access token. Only provide it for Track 1 SDKs.
        :param client_id:
        :param subscription_id:
        :param aux_subscriptions:
        :param aux_tenants:
        """
        resource = resource or self.cli_ctx.cloud.endpoints.active_directory_resource_id

        if aux_tenants and aux_subscriptions:
            raise CLIError("Please specify only one of aux_subscriptions and aux_tenants, not both")

        account = self.get_subscription(subscription_id)

        managed_identity_type, managed_identity_id = Profile._try_parse_msi_account_name(account)

        # Cloud Shell is just a system assignment managed identity
        if in_cloud_console() and account[_USER_ENTITY].get(_CLOUD_SHELL_ID):
            managed_identity_type = MsiAccountTypes.system_assigned

        if managed_identity_type is None:
            # user and service principal
            external_tenants = []
            if aux_tenants:
                external_tenants = [tenant for tenant in aux_tenants if tenant != account[_TENANT_ID]]
            if aux_subscriptions:
                ext_subs = [aux_sub for aux_sub in aux_subscriptions if aux_sub != subscription_id]
                for ext_sub in ext_subs:
                    sub = self.get_subscription(ext_sub)
                    if sub[_TENANT_ID] != account[_TENANT_ID]:
                        external_tenants.append(sub[_TENANT_ID])

            credential = self._create_credential(account, client_id=client_id)
            external_credentials = []
            for external_tenant in external_tenants:
                external_credentials.append(self._create_credential(account, external_tenant, client_id=client_id))
            from azure.cli.core.auth.credential_adaptor import CredentialAdaptor
            cred = CredentialAdaptor(credential,
                                     auxiliary_credentials=external_credentials,
                                     resource=resource)
        else:
            # managed identity
            cred = MsiAccountTypes.msi_auth_factory(managed_identity_type, managed_identity_id, resource)
        return (cred,
                str(account[_SUBSCRIPTION_ID]),
                str(account[_TENANT_ID]))

    def test_get_raw_token(self, resource=None, scopes=None, subscription=None, tenant=None):
        # Convert resource to scopes
        if resource and not scopes:
            from .auth.util import resource_to_scopes
            scopes = resource_to_scopes(resource)

        # Use ARM as the default scopes
        if not scopes:
            scopes = self._arm_scope

        if subscription and tenant:
            raise CLIError("Please specify only one of subscription and tenant, not both")

        account = self.get_subscription(subscription)

        identity_type, identity_id = Profile._try_parse_msi_account_name(account)
        if identity_type:
            # managed identity
            if tenant:
                raise CLIError("Tenant shouldn't be specified for managed identity account")
            from .auth.util import scopes_to_resource
            msi_creds = MsiAccountTypes.msi_auth_factory(identity_type, identity_id,
                                                         scopes_to_resource(scopes))
            sdk_token = msi_creds.get_token(*scopes)
        elif in_cloud_console() and account[_USER_ENTITY].get(_CLOUD_SHELL_ID):
            # Cloud Shell, which is just a system-assigned managed identity.
            if tenant:
                raise CLIError("Tenant shouldn't be specified for Cloud Shell account")
            from .auth.util import scopes_to_resource
            msi_creds = MsiAccountTypes.msi_auth_factory(MsiAccountTypes.system_assigned, identity_id,
                                                         scopes_to_resource(scopes))
            sdk_token = msi_creds.get_token(*scopes)
        else:
            credential = self._create_credential(account, tenant)
            sdk_token = credential.get_token(*scopes)

        # Convert epoch int 'expires_on' to datetime string 'expiresOn' for backward compatibility
        # WARNING: expiresOn is deprecated and will be removed in future release.
        import datetime
        expiresOn = datetime.datetime.fromtimestamp(sdk_token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f")

        token_entry = {
            'accessToken': sdk_token.token,
            'expires_on': sdk_token.expires_on,  # epoch int, like 1605238724
            'expiresOn': expiresOn  # datetime string, like "2020-11-12 13:50:47.114324"
        }

        # (tokenType, accessToken, tokenEntry)
        creds = 'Bearer', sdk_token.token, token_entry

        # (cred, subscription, tenant)
        return (creds,
                None if tenant else str(account[_SUBSCRIPTION_ID]),
                str(tenant if tenant else account[_TENANT_ID]))

    def test_normalize_properties(self, user, subscriptions, is_service_principal, cert_sn_issuer_auth=None,
                              user_assigned_identity_id=None):
        consolidated = []
        for s in subscriptions:
            subscription_dict = {
                _SUBSCRIPTION_ID: s.id.rpartition('/')[2],
                _SUBSCRIPTION_NAME: s.display_name,
                _STATE: s.state,
                _USER_ENTITY: {
                    _USER_NAME: user,
                    _USER_TYPE: _SERVICE_PRINCIPAL if is_service_principal else _USER
                },
                _IS_DEFAULT_SUBSCRIPTION: False,
                _TENANT_ID: s.tenant_id,
                _ENVIRONMENT_NAME: self.cli_ctx.cloud.name
            }

            if subscription_dict[_SUBSCRIPTION_NAME] != _TENANT_LEVEL_ACCOUNT_NAME:
                _transform_subscription_for_multiapi(s, subscription_dict)

            consolidated.append(subscription_dict)

            if cert_sn_issuer_auth:
                consolidated[-1][_USER_ENTITY][_SERVICE_PRINCIPAL_CERT_SN_ISSUER_AUTH] = True
            if user_assigned_identity_id:
                consolidated[-1][_USER_ENTITY][_ASSIGNED_IDENTITY_INFO] = user_assigned_identity_id

        return consolidated

    def test_build_tenant_level_accounts(self, tenants):
        result = []
        for t in tenants:
            s = self._new_account()
            s.id = '/subscriptions/' + t
            s.subscription = t
            s.tenant_id = t
            s.display_name = _TENANT_LEVEL_ACCOUNT_NAME
            result.append(s)
        return result

    def test_new_account(self):
        """Build an empty Subscription which will be used as a tenant account.
        API version doesn't matter as only specified attributes are preserved by _normalize_properties."""
        from azure.cli.core.profiles import ResourceType, get_sdk
        SubscriptionType = get_sdk(self.cli_ctx, ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS,
                                   'Subscription', mod='models')
        s = SubscriptionType()
        s.state = 'Enabled'
        return s

    def test_set_subscriptions(self, new_subscriptions, merge=True, secondary_key_name=None):

        def _get_key_name(account, secondary_key_name):
            return (account[_SUBSCRIPTION_ID] if secondary_key_name is None
                    else '{}-{}'.format(account[_SUBSCRIPTION_ID], account[secondary_key_name]))

        def _match_account(account, subscription_id, secondary_key_name, secondary_key_val):
            return (account[_SUBSCRIPTION_ID] == subscription_id and
                    (secondary_key_val is None or account[secondary_key_name] == secondary_key_val))

        existing_ones = self.load_cached_subscriptions(all_clouds=True)
        active_one = next((x for x in existing_ones if x.get(_IS_DEFAULT_SUBSCRIPTION)), None)
        active_subscription_id = active_one[_SUBSCRIPTION_ID] if active_one else None
        active_secondary_key_val = active_one[secondary_key_name] if (active_one and secondary_key_name) else None
        active_cloud = self.cli_ctx.cloud
        default_sub_id = None

        # merge with existing ones
        if merge:
            dic = {_get_key_name(x, secondary_key_name): x for x in existing_ones}
        else:
            dic = {}

        dic.update((_get_key_name(x, secondary_key_name), x) for x in new_subscriptions)
        subscriptions = list(dic.values())
        if subscriptions:
            if active_one:
                new_active_one = next(
                    (x for x in new_subscriptions if _match_account(x, active_subscription_id, secondary_key_name,
                                                                    active_secondary_key_val)), None)

                for s in subscriptions:
                    s[_IS_DEFAULT_SUBSCRIPTION] = False

                if not new_active_one:
                    new_active_one = Profile._pick_working_subscription(new_subscriptions)
            else:
                new_active_one = Profile._pick_working_subscription(new_subscriptions)

            new_active_one[_IS_DEFAULT_SUBSCRIPTION] = True
            default_sub_id = new_active_one[_SUBSCRIPTION_ID]

            set_cloud_subscription(self.cli_ctx, active_cloud.name, default_sub_id)
        self._storage[_SUBSCRIPTIONS] = subscriptions

    def test_pick_working_subscription(subscriptions):
        s = next((x for x in subscriptions if x.get(_STATE) == 'Enabled'), None)
        return s or subscriptions[0]

    def test_is_tenant_level_account(self):
        return self.get_subscription()[_SUBSCRIPTION_NAME] == _TENANT_LEVEL_ACCOUNT_NAME

    def test_set_active_subscription(self, subscription):  # take id or name
        subscriptions = self.load_cached_subscriptions(all_clouds=True)
        active_cloud = self.cli_ctx.cloud
        subscription = subscription.lower()
        result = [x for x in subscriptions
                  if subscription in [x[_SUBSCRIPTION_ID].lower(),
                                      x[_SUBSCRIPTION_NAME].lower()] and
                  x[_ENVIRONMENT_NAME] == active_cloud.name]

        if len(result) != 1:
            raise CLIError("The subscription of '{}' {} in cloud '{}'.".format(
                subscription, "doesn't exist" if not result else 'has more than one match', active_cloud.name))

        for s in subscriptions:
            s[_IS_DEFAULT_SUBSCRIPTION] = False
        result[0][_IS_DEFAULT_SUBSCRIPTION] = True

        set_cloud_subscription(self.cli_ctx, active_cloud.name, result[0][_SUBSCRIPTION_ID])
        self._storage[_SUBSCRIPTIONS] = subscriptions

    def test_load_cached_subscriptions(self, all_clouds=False):
        subscriptions = self._storage.get(_SUBSCRIPTIONS) or []
        active_cloud = self.cli_ctx.cloud
        cached_subscriptions = [sub for sub in subscriptions
                                if all_clouds or sub[_ENVIRONMENT_NAME] == active_cloud.name]
        # use deepcopy as we don't want to persist these changes to file.
        return deepcopy(cached_subscriptions)

    def test_get_current_account_user(self):
        try:
            active_account = self.get_subscription()
        except CLIError:
            raise CLIError('There are no active accounts.')

        return active_account[_USER_ENTITY][_USER_NAME]

    def test_get_subscription(self, subscription=None):  # take id or name
        subscriptions = self.load_cached_subscriptions()
        if not subscriptions:
            raise CLIError(_AZ_LOGIN_MESSAGE)

        result = [x for x in subscriptions if (
            not subscription and x.get(_IS_DEFAULT_SUBSCRIPTION) or
            subscription and subscription.lower() in [x[_SUBSCRIPTION_ID].lower(), x[
                _SUBSCRIPTION_NAME].lower()])]
        if not result and subscription:
            raise CLIError("Subscription '{}' not found. "
                           "Check the spelling and casing and try again.".format(subscription))
        if not result and not subscription:
            raise CLIError("No subscription found. Run 'az account set' to select a subscription.")
        if len(result) > 1:
            raise CLIError("Multiple subscriptions with the name '{}' found. "
                           "Specify the subscription ID.".format(subscription))
        return result[0]

    def test_get_subscription_id(self, subscription=None):  # take id or name
        return self.get_subscription(subscription)[_SUBSCRIPTION_ID]

    def test_try_parse_msi_account_name(account):
        msi_info, user = account[_USER_ENTITY].get(_ASSIGNED_IDENTITY_INFO), account[_USER_ENTITY].get(_USER_NAME)

        if user in [_SYSTEM_ASSIGNED_IDENTITY, _USER_ASSIGNED_IDENTITY]:
            if not msi_info:
                msi_info = account[_SUBSCRIPTION_NAME]  # fall back to old persisting way
            parts = msi_info.split('-', 1)
            if parts[0] in MsiAccountTypes.valid_msi_account_types():
                return parts[0], (None if len(parts) <= 1 else parts[1])
        return None, None

    def test_create_credential(self, account, tenant_id=None, client_id=None):
        """Create a credential object driven by MSAL

        :param account:
        :param tenant_id: If not None, override tenantId from 'account'
        :param client_id:
        :return:
        """
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        tenant_id = tenant_id if tenant_id else account[_TENANT_ID]
        identity = _create_identity_instance(self.cli_ctx, self._authority, tenant_id=tenant_id, client_id=client_id)

        # User
        if user_type == _USER:
            return identity.get_user_credential(username_or_sp_id)

        # Service Principal
        if user_type == _SERVICE_PRINCIPAL:
            return identity.get_service_principal_credential(username_or_sp_id)

        raise NotImplementedError

    def test_refresh_accounts(self):
        subscriptions = self.load_cached_subscriptions()
        to_refresh = subscriptions

        subscription_finder = SubscriptionFinder(self.cli_ctx)
        refreshed_list = set()
        result = []
        for s in to_refresh:
            user_name = s[_USER_ENTITY][_USER_NAME]
            if user_name in refreshed_list:
                continue
            refreshed_list.add(user_name)
            is_service_principal = (s[_USER_ENTITY][_USER_TYPE] == _SERVICE_PRINCIPAL)
            tenant = s[_TENANT_ID]
            subscriptions = []
            try:
                identity_credential = self._create_credential(s, tenant)
                if is_service_principal:
                    subscriptions = subscription_finder.find_using_specific_tenant(tenant, identity_credential)
                else:
                    # pylint: disable=protected-access
                    subscriptions = subscription_finder.find_using_common_tenant(user_name, identity_credential)
            except Exception as ex:  # pylint: disable=broad-except
                logger.warning("Refreshing for '%s' failed with an error '%s'. The existing accounts were not "
                               "modified. You can run 'az login' later to explicitly refresh them", user_name, ex)
                result += deepcopy([r for r in to_refresh if r[_USER_ENTITY][_USER_NAME] == user_name])
                continue

            if not subscriptions:
                if s[_SUBSCRIPTION_NAME] == _TENANT_LEVEL_ACCOUNT_NAME:
                    subscriptions = self._build_tenant_level_accounts([s[_TENANT_ID]])

                if not subscriptions:
                    continue

            consolidated = self._normalize_properties(user_name,
                                                      subscriptions,
                                                      is_service_principal)
            result += consolidated

        self._set_subscriptions(result, merge=False)

    def test_get_sp_auth_info(self, subscription_id=None, name=None, password=None, cert_file=None):
        """Generate a JSON for --json-auth argument when used in:
            - az ad sp create-for-rbac --json-auth
        """
        from collections import OrderedDict
        account = self.get_subscription(subscription_id)

        # is the credential created through command like 'create-for-rbac'?
        result = OrderedDict()

        result['clientId'] = name
        if password:
            result['clientSecret'] = password
        else:
            result['clientCertificate'] = cert_file
        result['subscriptionId'] = subscription_id or account[_SUBSCRIPTION_ID]

        result[_TENANT_ID] = account[_TENANT_ID]
        endpoint_mappings = OrderedDict()  # use OrderedDict to control the output sequence
        endpoint_mappings['active_directory'] = 'activeDirectoryEndpointUrl'
        endpoint_mappings['resource_manager'] = 'resourceManagerEndpointUrl'
        endpoint_mappings['active_directory_graph_resource_id'] = 'activeDirectoryGraphResourceId'
        endpoint_mappings['sql_management'] = 'sqlManagementEndpointUrl'
        endpoint_mappings['gallery'] = 'galleryEndpointUrl'
        endpoint_mappings['management'] = 'managementEndpointUrl'
        from azure.cli.core.cloud import CloudEndpointNotSetException
        for e in endpoint_mappings:
            try:
                result[endpoint_mappings[e]] = getattr(get_active_cloud(self.cli_ctx).endpoints, e)
            except CloudEndpointNotSetException:
                result[endpoint_mappings[e]] = None
        return result

    def test_get_installation_id(self):
        installation_id = self._storage.get(_INSTALLATION_ID)
        if not installation_id:
            try:
                # We share the same installationId with Azure Powershell. So try to load installationId from PSH file
                # Contact: DEV@Nanxiang Liu, PM@Damien Caro
                shared_installation_id_file = os.path.join(self.cli_ctx.config.config_dir,
                                                           'AzureRmContextSettings.json')
                with open(shared_installation_id_file, 'r', encoding='utf-8-sig') as f:
                    import json
                    content = json.load(f)
                    installation_id = content['Settings']['InstallationId']
            except Exception as ex:  # pylint: disable=broad-except
                logger.debug('Failed to load installationId from AzureRmSurvey.json. %s', str(ex))
                import uuid
                installation_id = str(uuid.uuid1())
            self._storage[_INSTALLATION_ID] = installation_id
        return installation_id

    def test_clear_sessions(self):
        """Clear existing Azure CLI sessions."""
        self._storage[_SUBSCRIPTIONS] = []

    def test_login_with_clear_sessions(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)

        # Mock the login method to return a sample subscription
        profile.login = mock.MagicMock(return_value=[{
            'id': '1',
            'name': 'Test Subscription',
            'state': 'Enabled',
            'user': {
                'name': 'test_user',
                'type': 'user'
            },
            'isDefault': True,
            'tenantId': 'test_tenant',
            'environmentName': 'AzureCloud'
        }])

        # Call the login method
        subs = profile.login(True, None, None, False, None, use_device_code=False, allow_no_subscriptions=False)

        # Assert that the clear_sessions method was called
        profile.clear_sessions.assert_called_once()

        # Assert that the login method returned the expected subscription
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0]['name'], 'Test Subscription')

class FileHandleStub(object):  # pylint: disable=too-few-public-methods

    def write(self, content):
        pass

    def __enter__(self):
        return self

    def __exit__(self, _2, _3, _4):
        pass


class SubscriptionStub(Subscription):  # pylint: disable=too-few-public-methods

    def __init__(self, id, display_name, state, tenant_id, managed_by_tenants=[], home_tenant_id=None,
                 tenant_display_name=None, tenant_default_domain=None):  # pylint: disable=redefined-builtin
        policies = SubscriptionPolicies()
        policies.spending_limit = SpendingLimit.current_period_off
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

        # Below attributes are added by CLI. Without them, this denotes a Subscription from SDK
        if home_tenant_id:
            self.home_tenant_id = home_tenant_id
        if tenant_display_name:
            self.tenant_display_name = tenant_display_name
        if tenant_default_domain:
            self.tenant_default_domain = tenant_default_domain


class ManagedByTenantStub(ManagedByTenant):  # pylint: disable=too-few-public-methods

    def __init__(self, tenant_id):  # pylint: disable=redefined-builtin
        self.tenant_id = tenant_id


class TenantStub(object):  # pylint: disable=too-few-public-methods

    def __init__(self, tenant_id, display_name=MOCK_TENANT_DISPLAY_NAME, default_domain=MOCK_TENANT_DEFAULT_DOMAIN):
        self.tenant_id = tenant_id
        self.display_name = display_name
        self.default_domain = default_domain
        self.additional_properties = {}


class TestUtils(unittest.TestCase):
    def test_attach_token_tenant_v2016_06_01(self):
        from azure.mgmt.resource.subscriptions.v2016_06_01.models import Subscription
        subscription = Subscription()
        _attach_token_tenant(subscription, "token_tenant_1")
        self.assertEqual(subscription.tenant_id, "token_tenant_1")
        self.assertFalse(hasattr(subscription, "home_tenant_id"))

    def test_attach_token_tenant_v2022_12_01(self):
        from azure.mgmt.resource.subscriptions.v2022_12_01.models import Subscription
        subscription = Subscription()
        subscription.tenant_id = "home_tenant_1"
        _attach_token_tenant(subscription, "token_tenant_1")
        self.assertEqual(subscription.tenant_id, "token_tenant_1")
        self.assertEqual(subscription.home_tenant_id, "home_tenant_1")

    def test_transform_subscription_for_multiapi(self):

        class SimpleSubscription:
            pass

        class SimpleManagedByTenant:
            pass

        tenant_id = "00000001-0000-0000-0000-000000000000"

        # No 2019-06-01 property is set.
        s = SimpleSubscription()
        d = {}
        _transform_subscription_for_multiapi(s, d)
        assert d == {}

        # home_tenant_id is set.
        s = SimpleSubscription()
        s.home_tenant_id = tenant_id
        d = {}
        _transform_subscription_for_multiapi(s, d)
        assert d == {'homeTenantId': '00000001-0000-0000-0000-000000000000'}

        # managed_by_tenants is set, but is None. It is still preserved.
        s = SimpleSubscription()
        s.managed_by_tenants = None
        d = {}
        _transform_subscription_for_multiapi(s, d)
        assert d == {'managedByTenants': None}

        # managed_by_tenants is set, but is []. It is still preserved.
        s = SimpleSubscription()
        s.managed_by_tenants = []
        d = {}
        _transform_subscription_for_multiapi(s, d)
        assert d == {'managedByTenants': []}

        # managed_by_tenants is set, and has valid items. It is preserved.
        s = SimpleSubscription()
        t = SimpleManagedByTenant()
        t.tenant_id = tenant_id
        s.managed_by_tenants = [t]
        d = {}
        _transform_subscription_for_multiapi(s, d)
        assert d == {'managedByTenants': [{"tenantId": tenant_id}]}


if __name__ == '__main__':
    unittest.main()
