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
        self.assertEqual(self.subscription1_output, subs)

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
        self.assertEqual(self.subscription1_output, subs)

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

        self.assertEqual(self.subscription1_output, subs)

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
        cli = DummyCli()

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        user = profile.get_current_account_user()

        self.assertEqual(user, self.user1)

    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', return_value=credential_mock)
    def test_get_login_credentials(self, get_user_credential_mock):
        cli = DummyCli()
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_subscription = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id),
                                             'MSI-DEV-INC', self.state1, '12345678-38d6-4fb2-bad9-b7b93a3e1234')
        consolidated = profile._normalize_properties(self.user1,
                                                     [test_subscription],
                                                     False, None, None)
        profile._set_subscriptions(consolidated)
        # action
        cred, subscription_id, _ = profile.get_login_credentials()
        get_user_credential_mock.assert_called_with(self.user1)

        # verify
        self.assertEqual(subscription_id, test_subscription_id)

        # verify the cred.get_token()
        token = cred.get_token()
        self.assertEqual(token.token, MOCK_ACCESS_TOKEN)

    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', return_value=credential_mock)
    def test_get_login_credentials_aux_subscriptions(self, get_user_credential_mock):
        cli = DummyCli()

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        test_subscription_id1 = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_subscription_id2 = '12345678-1bf0-4dda-aec3-cb9272f09591'
        test_tenant_id1 = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_tenant_id2 = '12345678-38d6-4fb2-bad9-b7b93a3e4321'
        test_subscription1 = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id1),
                                             'MSI-DEV-INC', self.state1, test_tenant_id1)
        test_subscription2 = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id2),
                                              'MSI-DEV-INC2', self.state1, test_tenant_id2)
        consolidated = profile._normalize_properties(self.user1,
                                                     [test_subscription1, test_subscription2],
                                                     False, None, None)
        profile._set_subscriptions(consolidated)

        cred, subscription_id, _ = profile.get_login_credentials(subscription_id=test_subscription_id1,
                                                                 aux_subscriptions=[test_subscription_id2])

        self.assertEqual(subscription_id, test_subscription_id1)

        token = cred.get_token()
        aux_tokens = cred.get_auxiliary_tokens()
        self.assertEqual(token.token, MOCK_ACCESS_TOKEN)
        self.assertEqual(aux_tokens[0].token, MOCK_ACCESS_TOKEN)

    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', return_value=credential_mock)
    def test_get_login_credentials_aux_tenants(self, get_user_credential_mock):
        cli = DummyCli()

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        test_subscription_id1 = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_subscription_id2 = '12345678-1bf0-4dda-aec3-cb9272f09591'
        test_tenant_id1 = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_tenant_id2 = '12345678-38d6-4fb2-bad9-b7b93a3e4321'
        test_subscription = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id1),
                                             'MSI-DEV-INC', self.state1, test_tenant_id1)
        test_subscription2 = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id2),
                                              'MSI-DEV-INC2', self.state1, test_tenant_id2)
        consolidated = profile._normalize_properties(self.user1,
                                                     [test_subscription, test_subscription2],
                                                     False, None, None)
        profile._set_subscriptions(consolidated)
        # test only input aux_tenants
        cred, subscription_id, _ = profile.get_login_credentials(subscription_id=test_subscription_id1,
                                                                 aux_tenants=[test_tenant_id2])

        self.assertEqual(subscription_id, test_subscription_id1)

        token = cred.get_token()
        aux_tokens = cred.get_auxiliary_tokens()
        self.assertEqual(token.token, MOCK_ACCESS_TOKEN)
        self.assertEqual(aux_tokens[0].token, MOCK_ACCESS_TOKEN)

        # test input aux_tenants and aux_subscriptions
        with self.assertRaisesRegex(CLIError,
                                     "Please specify only one of aux_subscriptions and aux_tenants, not both"):
            cred, subscription_id, _ = profile.get_login_credentials(subscription_id=test_subscription_id1,
                                                                     aux_subscriptions=[test_subscription_id2],
                                                                     aux_tenants=[test_tenant_id2])

    @mock.patch('azure.cli.core.auth.adal_authentication.MSIAuthenticationWrapper', MSRestAzureAuthStub)
    def test_get_login_credentials_msi_system_assigned(self):

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None})
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_user = 'systemAssignedIdentity'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id, 'MSI', self.state1, test_tenant_id)
        consolidated = profile._normalize_properties(test_user,
                                                     [msi_subscription],
                                                     True)
        profile._set_subscriptions(consolidated)

        cred, subscription_id, _ = profile.get_login_credentials()

        self.assertEqual(subscription_id, test_subscription_id)

        # sniff test the msi_auth object
        cred.set_token()
        cred.token
        self.assertTrue(cred.set_token_invoked_count)
        self.assertTrue(cred.token_read_count)

    @mock.patch('azure.cli.core.auth.adal_authentication.MSIAuthenticationWrapper', MSRestAzureAuthStub)
    def test_get_login_credentials_msi_user_assigned_with_client_id(self):
        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None})
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_user = 'userAssignedIdentity'
        test_client_id = '12345678-38d6-4fb2-bad9-b7b93a3e8888'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id, 'MSIClient-{}'.format(test_client_id), self.state1, test_tenant_id)
        consolidated = profile._normalize_properties(test_user, [msi_subscription], True)
        profile._set_subscriptions(consolidated, secondary_key_name='name')

        cred, subscription_id, _ = profile.get_login_credentials()

        self.assertEqual(subscription_id, test_subscription_id)

        # sniff test the msi_auth object
        cred.set_token()
        cred.token
        self.assertTrue(cred.set_token_invoked_count)
        self.assertTrue(cred.token_read_count)
        self.assertTrue(cred.client_id, test_client_id)

    @mock.patch('azure.cli.core.auth.adal_authentication.MSIAuthenticationWrapper', MSRestAzureAuthStub)
    def test_get_login_credentials_msi_user_assigned_with_object_id(self):

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None})
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_object_id = '12345678-38d6-4fb2-bad9-b7b93a3e9999'
        msi_subscription = SubscriptionStub('/subscriptions/12345678-1bf0-4dda-aec3-cb9272f09590',
                                            'MSIObject-{}'.format(test_object_id),
                                            self.state1, '12345678-38d6-4fb2-bad9-b7b93a3e1234')
        consolidated = profile._normalize_properties('userAssignedIdentity', [msi_subscription], True)
        profile._set_subscriptions(consolidated, secondary_key_name='name')

        cred, subscription_id, _ = profile.get_login_credentials()

        self.assertEqual(subscription_id, test_subscription_id)

        # sniff test the msi_auth object
        cred.set_token()
        cred.token
        self.assertTrue(cred.set_token_invoked_count)
        self.assertTrue(cred.token_read_count)
        self.assertTrue(cred.object_id, test_object_id)

    @mock.patch('azure.cli.core.auth.adal_authentication.MSIAuthenticationWrapper', MSRestAzureAuthStub)
    def test_get_login_credentials_msi_user_assigned_with_res_id(self):
        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None})
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_res_id = ('/subscriptions/{}/resourceGroups/r1/providers/Microsoft.ManagedIdentity/'
                       'userAssignedIdentities/id1').format(test_subscription_id)
        msi_subscription = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id),
                                            'MSIResource-{}'.format(test_res_id),
                                            self.state1, '12345678-38d6-4fb2-bad9-b7b93a3e1234')
        consolidated = profile._normalize_properties('userAssignedIdentity', [msi_subscription], True)
        profile._set_subscriptions(consolidated, secondary_key_name='name')

        cred, subscription_id, _ = profile.get_login_credentials()

        self.assertEqual(subscription_id, test_subscription_id)

        # sniff test the msi_auth object
        cred.set_token()
        cred.token
        self.assertTrue(cred.set_token_invoked_count)
        self.assertTrue(cred.token_read_count)
        self.assertTrue(cred.msi_res_id, test_res_id)

    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential')
    def test_get_raw_token(self, get_user_credential_mock):
        credential_mock_temp = CredentialMock()
        get_user_credential_mock.return_value = credential_mock_temp
        cli = DummyCli()
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False, None, None)
        profile._set_subscriptions(consolidated)

        # action
        # Get token with ADAL-style resource
        resource_result = profile.get_raw_token(resource=self.adal_resource)
        # Get token with MSAL-style scopes
        scopes_result = profile.get_raw_token(scopes=self.msal_scopes)

        # verify
        self.assertEqual(resource_result, scopes_result)
        creds, sub, tenant = scopes_result

        self.assertEqual(creds[0], 'Bearer')
        self.assertEqual(creds[1], MOCK_ACCESS_TOKEN)
        self.assertEqual(creds[2]['expires_on'], MOCK_EXPIRES_ON_INT)
        self.assertEqual(creds[2]['expiresOn'], MOCK_EXPIRES_ON_DATETIME)

        # subscription should be set
        self.assertEqual(sub, self.subscription1.subscription_id)
        self.assertEqual(tenant, self.tenant_id)

        # Test get_raw_token with tenant
        creds, sub, tenant = profile.get_raw_token(resource=self.adal_resource, tenant=self.tenant_id)

        # verify
        assert list(credential_mock_temp.get_token_scopes) == self.msal_scopes

        self.assertEqual(creds[0], 'Bearer')
        self.assertEqual(creds[1], MOCK_ACCESS_TOKEN)
        self.assertEqual(creds[2]['expires_on'], MOCK_EXPIRES_ON_INT)
        self.assertEqual(creds[2]['expiresOn'], MOCK_EXPIRES_ON_DATETIME)

        # subscription shouldn't be set
        self.assertIsNone(sub)
        self.assertEqual(tenant, self.tenant_id)

    @mock.patch('azure.cli.core.auth.identity.Identity.get_service_principal_credential')
    def test_get_raw_token_for_sp(self, get_service_principal_credential_mock):
        credential_mock_temp = CredentialMock()
        get_service_principal_credential_mock.return_value = credential_mock_temp
        cli = DummyCli()
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        consolidated = profile._normalize_properties('sp1',
                                                     [self.subscription1],
                                                     True)
        profile._set_subscriptions(consolidated)
        # action
        creds, sub, tenant = profile.get_raw_token(resource=self.adal_resource)

        # verify
        assert list(credential_mock_temp.get_token_scopes) == self.msal_scopes

        self.assertEqual(creds[0], BEARER)
        self.assertEqual(creds[1], MOCK_ACCESS_TOKEN)
        # the last in the tuple is the whole token entry which has several fields
        self.assertEqual(creds[2]['expires_on'], MOCK_EXPIRES_ON_INT)
        self.assertEqual(creds[2]['expiresOn'], MOCK_EXPIRES_ON_DATETIME)

        # subscription should be set
        self.assertEqual(sub, self.subscription1.subscription_id)
        self.assertEqual(tenant, self.tenant_id)

        # Test get_raw_token with tenant
        creds, sub, tenant = profile.get_raw_token(resource=self.adal_resource, tenant=self.tenant_id)

        self.assertEqual(creds[0], BEARER)
        self.assertEqual(creds[1], MOCK_ACCESS_TOKEN)
        self.assertEqual(creds[2]['expires_on'], MOCK_EXPIRES_ON_INT)
        self.assertEqual(creds[2]['expiresOn'], MOCK_EXPIRES_ON_DATETIME)

        # subscription shouldn't be set
        self.assertIsNone(sub)
        self.assertEqual(tenant, self.tenant_id)

    @mock.patch('azure.cli.core.auth.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    def test_get_raw_token_msi_system_assigned(self, mock_msi_auth):
        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None})
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_user = 'systemAssignedIdentity'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id,
                                            'MSI', self.state1, test_tenant_id)
        consolidated = profile._normalize_properties(test_user,
                                                     [msi_subscription],
                                                     True)
        profile._set_subscriptions(consolidated)

        mi_auth_instance = None

        def mi_auth_factory(*args, **kwargs):
            nonlocal mi_auth_instance
            mi_auth_instance = MSRestAzureAuthStub(*args, **kwargs)
            return mi_auth_instance

        mock_msi_auth.side_effect = mi_auth_factory

        # action
        cred, subscription_id, tenant_id = profile.get_raw_token(resource=self.adal_resource)

        # Make sure resource/scopes are passed to MSIAuthenticationWrapper
        assert mi_auth_instance.resource == self.adal_resource
        assert list(mi_auth_instance.get_token_scopes) == self.msal_scopes

        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(cred[0], 'Bearer')
        self.assertEqual(cred[1], TestProfile.test_msi_access_token)

        # Make sure expires_on and expiresOn are set
        self.assertEqual(cred[2]['expires_on'], MOCK_EXPIRES_ON_INT)
        self.assertEqual(cred[2]['expiresOn'], MOCK_EXPIRES_ON_DATETIME)
        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(tenant_id, test_tenant_id)

        # verify tenant shouldn't be specified for MSI account
        with self.assertRaisesRegex(CLIError, "Tenant shouldn't be specified"):
            cred, subscription_id, _ = profile.get_raw_token(resource='http://test_resource', tenant=self.tenant_id)

    @mock.patch('azure.cli.core._profile.in_cloud_console', autospec=True)
    @mock.patch('azure.cli.core.auth.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    def test_get_raw_token_in_cloud_console(self, mock_msi_auth, mock_in_cloud_console):
        mock_in_cloud_console.return_value = True

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None})
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id,
                                            self.display_name1, self.state1, test_tenant_id)
        consolidated = profile._normalize_properties(self.user1,
                                                     [msi_subscription],
                                                     True)
        consolidated[0]['user']['cloudShellID'] = True
        profile._set_subscriptions(consolidated)

        mi_auth_instance = None

        def mi_auth_factory(*args, **kwargs):
            nonlocal mi_auth_instance
            mi_auth_instance = MSRestAzureAuthStub(*args, **kwargs)
            return mi_auth_instance

        mock_msi_auth.side_effect = mi_auth_factory

        # action
        cred, subscription_id, tenant_id = profile.get_raw_token(resource=self.adal_resource)

        # Make sure resource/scopes are passed to MSIAuthenticationWrapper
        assert mi_auth_instance.resource == self.adal_resource
        assert list(mi_auth_instance.get_token_scopes) == self.msal_scopes

        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(cred[0], 'Bearer')
        self.assertEqual(cred[1], TestProfile.test_msi_access_token)

        # Make sure expires_on and expiresOn are set
        self.assertEqual(cred[2]['expires_on'], MOCK_EXPIRES_ON_INT)
        self.assertEqual(cred[2]['expiresOn'], MOCK_EXPIRES_ON_DATETIME)
        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(tenant_id, test_tenant_id)

        # verify tenant shouldn't be specified for Cloud Shell account
        with self.assertRaisesRegex(CLIError, 'Cloud Shell'):
            cred, subscription_id, _ = profile.get_raw_token(resource='http://test_resource', tenant=self.tenant_id)

    @mock.patch('azure.cli.core.auth.identity.Identity.logout_user')
    def test_logout(self, logout_user_mock):
        cli = DummyCli()

        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        self.assertEqual(1, len(storage_mock['subscriptions']))
        # action
        profile.logout(self.user1)

        # verify
        self.assertEqual(0, len(storage_mock['subscriptions']))
        logout_user_mock.assert_called_with(self.user1)

    @mock.patch('azure.cli.core.auth.identity.Identity.logout_all_users')
    def test_logout_all(self, logout_all_users_mock):
        cli = DummyCli()
        # setup
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        consolidated2 = profile._normalize_properties(self.user2,
                                                      [self.subscription2],
                                                      False)
        profile._set_subscriptions(consolidated + consolidated2)

        self.assertEqual(2, len(storage_mock['subscriptions']))
        # action
        profile.logout_all()

        # verify
        self.assertEqual([], storage_mock['subscriptions'])
        logout_all_users_mock.assert_called_once()

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    def test_refresh_accounts_one_user_account(self, get_user_credential_mock, create_subscription_client_mock):
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        create_subscription_client_mock.return_value = mock_arm_client

        cli = DummyCli()
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        consolidated = profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False, None, None)
        profile._set_subscriptions(consolidated)

        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = deepcopy([self.subscription1_raw, self.subscription2_raw])

        profile.refresh_accounts()

        # assert
        result = storage_mock['subscriptions']
        self.assertEqual(2, len(result))
        self.assertEqual(self.id1.split('/')[-1], result[0]['id'])
        assert result[0]['user']['name'] == self.user1
        assert result[0]['user']['type'] == 'user'

        self.assertEqual(self.id2.split('/')[-1], result[1]['id'])
        assert result[1]['user']['name'] == self.user1
        assert result[1]['user']['type'] == 'user'

        self.assertTrue(result[0]['isDefault'])

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_service_principal_credential', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    def test_refresh_accounts_one_user_account_one_sp_account(self, get_user_credential_mock,
                                                              get_service_principal_credential_mock,
                                                              create_subscription_client_mock):
        cli = DummyCli()
        sp_id = '44fee498-c798-4ebb-a41f-7bb523bed8d8'
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        sp_subscription1 = SubscriptionStub('sp-sub/3', 'foo-subname', self.state1, 'footenant.onmicrosoft.com')
        consolidated = profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False, None, None)
        consolidated += profile._normalize_properties(sp_id, [sp_subscription1], True)
        profile._set_subscriptions(consolidated)

        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.side_effect = deepcopy(
            [[self.subscription1], [self.subscription2, sp_subscription1]])
        create_subscription_client_mock.return_value = mock_arm_client

        profile.refresh_accounts()

        result = storage_mock['subscriptions']
        self.assertEqual(3, len(result))
        self.assertEqual(self.id1.split('/')[-1], result[0]['id'])
        assert result[0]['user']['name'] == self.user1
        assert result[0]['user']['type'] == 'user'

        self.assertEqual(self.id2.split('/')[-1], result[1]['id'])
        assert result[1]['user']['name'] == sp_id
        assert result[1]['user']['type'] == 'servicePrincipal'

        self.assertEqual('3', result[2]['id'])
        self.assertTrue(result[0]['isDefault'])
        assert result[2]['user']['name'] == sp_id
        assert result[2]['user']['type'] == 'servicePrincipal'

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    def test_refresh_accounts_with_nothing(self, get_user_credential_mock, create_subscription_client_mock):
        cli = DummyCli()
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        consolidated = profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False, None, None)
        profile._set_subscriptions(consolidated)

        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = []
        create_subscription_client_mock.return_value = mock_arm_client

        profile.refresh_accounts()

        # assert
        result = storage_mock['subscriptions']
        self.assertEqual(0, len(result))

    @mock.patch('azure.cli.core._profile.SubscriptionFinder._create_subscription_client', autospec=True)
    @mock.patch('azure.cli.core.auth.identity.Identity.get_user_credential', autospec=True)
    def test_login_common_tenant_mfa_warning(self, get_user_credential_mock, create_subscription_client_mock):
        # Assume 2 tenants. Home tenant tenant1 doesn't require MFA, but tenant2 does
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        tenant2_mfa_id = 'tenant2-0000-0000-0000-000000000000'
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id), TenantStub(tenant2_mfa_id)]
        create_subscription_client_mock.return_value = mock_arm_client

        finder = SubscriptionFinder(cli)

        from azure.cli.core.azclierror import AuthenticationError
        error_description = ("AADSTS50076: Due to a configuration change made by your administrator, "
                             "or because you moved to a new location, you must use multi-factor "
                             "authentication to access '797f4846-ba00-4fd7-ba43-dac1f8f63013'.\n"
                             "Trace ID: 00000000-0000-0000-0000-000000000000\n"
                             "Correlation ID: 00000000-0000-0000-0000-000000000000\n"
                             "Timestamp: 2020-03-10 04:42:59Z")
        msal_result = {
            'error': 'interaction_required',
            'error_description': error_description,
            'error_codes':[50076],
            'timestamp': '2020-03-10 04:42:59Z',
            'trace_id': '00000000-0000-0000-0000-000000000000',
            'correlation_id': '00000000-0000-0000-0000-000000000000',
            'error_uri': 'https://login.microsoftonline.com/error?code=50076',
            'suberror': 'basic_action'
        }

        err = AuthenticationError(error_description, recommendation=None)

        # MFA error raised on the second call
        mock_arm_client.subscriptions.list.side_effect = [[deepcopy(self.subscription1_raw)], err]

        credential = mock.MagicMock()
        all_subscriptions = finder.find_using_common_tenant(self.user1, credential)

        # subscriptions are correctly returned
        self.assertEqual(all_subscriptions, [self.subscription1])

        # With pytest, use -o log_cli=True to manually check the log

    def test_get_auth_info_for_newly_created_service_principal(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock)
        consolidated = profile._normalize_properties(self.user1, [self.subscription1], False)
        profile._set_subscriptions(consolidated)

        # certificate
        extended_info = profile.get_sp_auth_info(name='1234', cert_file='/tmp/123.pem')

        self.assertEqual(self.id1.split('/')[-1], extended_info['subscriptionId'])
        self.assertEqual(self.tenant_id, extended_info['tenantId'])
        self.assertEqual('1234', extended_info['clientId'])
        self.assertEqual('/tmp/123.pem', extended_info['clientCertificate'])
        self.assertIsNone(extended_info.get('clientSecret', None))
        self.assertEqual('https://login.microsoftonline.com', extended_info['activeDirectoryEndpointUrl'])
        self.assertEqual('https://management.azure.com/', extended_info['resourceManagerEndpointUrl'])

        # secret
        extended_info = profile.get_sp_auth_info(name='1234', password='very_secret')
        self.assertEqual('very_secret', extended_info['clientSecret'])


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


class TestUtils(unittest.TestCase):
    def test_attach_token_tenant(self):
        from azure.mgmt.resource.subscriptions.v2016_06_01.models import Subscription \
            as Subscription_v2016_06_01
        subscription = Subscription_v2016_06_01()
        _attach_token_tenant(subscription, "token_tenant_1")
        self.assertEqual(subscription.tenant_id, "token_tenant_1")
        self.assertFalse(hasattr(subscription, "home_tenant_id"))

    def test_attach_token_tenant_v2016_06_01(self):
        from azure.mgmt.resource.subscriptions.v2019_11_01.models import Subscription \
            as Subscription_v2019_11_01
        subscription = Subscription_v2019_11_01()
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
