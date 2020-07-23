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

from copy import deepcopy

from adal import AdalError
from azure.mgmt.resource.subscriptions.models import \
    (SubscriptionState, Subscription, SubscriptionPolicies, SpendingLimit, ManagedByTenant)

from azure.cli.core._profile import (Profile, CredsCache, SubscriptionFinder,
                                     ServicePrincipalAuth, _AUTH_CTX_FACTORY)
from azure.cli.core.mock import DummyCli

from knack.util import CLIError


class TestProfile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tenant_id = 'microsoft.com'
        cls.user1 = 'foo@foo.com'
        cls.id1 = 'subscriptions/1'
        cls.display_name1 = 'foo account'
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
        # Dummy result of azure.cli.core._profile.SubscriptionFinder._find_using_specific_tenant
        # home_tenant_id is mapped from tenant_id
        # tenant_id denotes token tenant
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

    def test_normalize(self):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        expected = self.subscription1_normalized
        self.assertEqual(expected, consolidated[0])
        # verify serialization works
        self.assertIsNotNone(json.dumps(consolidated[0]))

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
        finder = SubscriptionFinder(cli, None, None, arm_client_factory=None)
        result = finder._arm_client_factory(mock.MagicMock())
        self.assertEqual(result.config.base_url, 'http://foo_arm')

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_get_auth_info_for_logged_in_service_principal(self, mock_auth_context):
        cli = DummyCli()
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        profile._management_resource_uri = 'https://management.core.windows.net/'
        profile.find_subscriptions_on_login(False, '1234', 'my-secret', True, self.tenant_id, use_device_code=False,
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

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_create_account_without_subscriptions_thru_service_principal(self, mock_auth_context):
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = []
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        profile._management_resource_uri = 'https://management.core.windows.net/'

        # action
        result = profile.find_subscriptions_on_login(False,
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

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_create_account_with_subscriptions_allow_no_subscriptions_thru_service_principal(self, mock_auth_context):
        """test subscription is returned even with --allow-no-subscriptions. """
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        profile._management_resource_uri = 'https://management.core.windows.net/'

        # action
        result = profile.find_subscriptions_on_login(False,
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

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_create_account_without_subscriptions_thru_common_tenant(self, mock_auth_context):
        mock_auth_context.acquire_token.return_value = self.token_entry1
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        cli = DummyCli()
        tenant_object = mock.MagicMock()
        tenant_object.id = "foo-bar"
        tenant_object.tenant_id = self.tenant_id
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = []
        mock_arm_client.tenants.list.return_value = (x for x in [tenant_object])

        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        profile._management_resource_uri = 'https://management.core.windows.net/'

        # action
        result = profile.find_subscriptions_on_login(False,
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

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_create_account_without_subscriptions_without_tenant(self, mock_auth_context):
        cli = DummyCli()
        finder = mock.MagicMock()
        finder.find_through_interactive_flow.return_value = []
        storage_mock = {'subscriptions': []}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        # action
        result = profile.find_subscriptions_on_login(True,
                                                     '1234',
                                                     'my-secret',
                                                     False,
                                                     None,
                                                     use_device_code=False,
                                                     allow_no_subscriptions=True,
                                                     subscription_finder=finder)

        # assert
        self.assertTrue(0 == len(result))

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_get_current_account_user(self, mock_read_cred_file):
        cli = DummyCli()
        # setup
        mock_read_cred_file.return_value = [TestProfile.token_entry1]

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

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', return_value=None)
    def test_create_token_cache(self, mock_read_file):
        cli = DummyCli()
        mock_read_file.return_value = []
        profile = Profile(cli_ctx=cli, use_global_creds_cache=False, async_persist=False)
        cache = profile._creds_cache.adal_token_cache
        self.assertFalse(cache.read_items())
        self.assertTrue(mock_read_file.called)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_load_cached_tokens(self, mock_read_file):
        cli = DummyCli()
        mock_read_file.return_value = [TestProfile.token_entry1]
        profile = Profile(cli_ctx=cli, use_global_creds_cache=False, async_persist=False)
        cache = profile._creds_cache.adal_token_cache
        matched = cache.find({
            "_authority": "https://login.microsoftonline.com/common",
            "_clientId": "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
            "userId": self.user1
        })
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]['accessToken'], self.raw_token1)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_login_credentials(self, mock_get_token, mock_read_cred_file):
        cli = DummyCli()
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [TestProfile.token_entry1]
        mock_get_token.return_value = (some_token_type, TestProfile.raw_token1)
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_subscription = SubscriptionStub('/subscriptions/{}'.format(test_subscription_id),
                                             'MSI-DEV-INC', self.state1, '12345678-38d6-4fb2-bad9-b7b93a3e1234')
        consolidated = profile._normalize_properties(self.user1,
                                                     [test_subscription],
                                                     False)
        profile._set_subscriptions(consolidated)
        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # verify
        self.assertEqual(subscription_id, test_subscription_id)

        # verify the cred._tokenRetriever is a working lambda
        token_type, token = cred._token_retriever()
        self.assertEqual(token, self.raw_token1)
        self.assertEqual(some_token_type, token_type)
        mock_get_token.assert_called_once_with(mock.ANY, self.user1, test_tenant_id,
                                               'https://management.core.windows.net/')
        self.assertEqual(mock_get_token.call_count, 1)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_login_credentials_aux_subscriptions(self, mock_get_token, mock_read_cred_file):
        cli = DummyCli()
        raw_token2 = 'some...secrets2'
        token_entry2 = {
            "resource": "https://management.core.windows.net/",
            "tokenType": "Bearer",
            "_authority": "https://login.microsoftonline.com/common",
            "accessToken": raw_token2,
        }
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [TestProfile.token_entry1, token_entry2]
        mock_get_token.side_effect = [(some_token_type, TestProfile.raw_token1), (some_token_type, raw_token2)]
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
                                                     False)
        profile._set_subscriptions(consolidated)
        # action
        cred, subscription_id, _ = profile.get_login_credentials(subscription_id=test_subscription_id,
                                                                 aux_subscriptions=[test_subscription_id2])

        # verify
        self.assertEqual(subscription_id, test_subscription_id)

        # verify the cred._tokenRetriever is a working lambda
        token_type, token = cred._token_retriever()
        self.assertEqual(token, self.raw_token1)
        self.assertEqual(some_token_type, token_type)

        token2 = cred._external_tenant_token_retriever()
        self.assertEqual(len(token2), 1)
        self.assertEqual(token2[0][1], raw_token2)

        self.assertEqual(mock_get_token.call_count, 2)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_login_credentials_aux_tenants(self, mock_get_token, mock_read_cred_file):
        cli = DummyCli()
        raw_token2 = 'some...secrets2'
        token_entry2 = {
            "resource": "https://management.core.windows.net/",
            "tokenType": "Bearer",
            "_authority": "https://login.microsoftonline.com/common",
            "accessToken": raw_token2,
        }
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [TestProfile.token_entry1, token_entry2]
        mock_get_token.side_effect = [(some_token_type, TestProfile.raw_token1), (some_token_type, raw_token2)]
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
                                                     False)
        profile._set_subscriptions(consolidated)
        # test only input aux_tenants
        cred, subscription_id, _ = profile.get_login_credentials(subscription_id=test_subscription_id,
                                                                 aux_tenants=[test_tenant_id2])

        # verify
        self.assertEqual(subscription_id, test_subscription_id)

        # verify the cred._tokenRetriever is a working lambda
        token_type, token = cred._token_retriever()
        self.assertEqual(token, self.raw_token1)
        self.assertEqual(some_token_type, token_type)

        token2 = cred._external_tenant_token_retriever()
        self.assertEqual(len(token2), 1)
        self.assertEqual(token2[0][1], raw_token2)

        self.assertEqual(mock_get_token.call_count, 2)

        # test input aux_tenants and aux_subscriptions
        with self.assertRaisesRegexp(CLIError,
                                     "Please specify only one of aux_subscriptions and aux_tenants, not both"):
            cred, subscription_id, _ = profile.get_login_credentials(subscription_id=test_subscription_id,
                                                                     aux_subscriptions=[test_subscription_id2],
                                                                     aux_tenants=[test_tenant_id2])

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    def test_get_login_credentials_msi_system_assigned(self, mock_msi_auth, mock_read_cred_file):
        mock_read_cred_file.return_value = []

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_user = 'systemAssignedIdentity'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id, 'MSI', self.state1, test_tenant_id)
        consolidated = profile._normalize_properties(test_user,
                                                     [msi_subscription],
                                                     True)
        profile._set_subscriptions(consolidated)

        mock_msi_auth.side_effect = MSRestAzureAuthStub

        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # assert
        self.assertEqual(subscription_id, test_subscription_id)

        # sniff test the msi_auth object
        cred.set_token()
        cred.token
        self.assertTrue(cred.set_token_invoked_count)
        self.assertTrue(cred.token_read_count)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    def test_get_login_credentials_msi_user_assigned_with_client_id(self, mock_msi_auth, mock_read_cred_file):
        mock_read_cred_file.return_value = []

        # setup an existing msi subscription
        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_user = 'userAssignedIdentity'
        test_client_id = '12345678-38d6-4fb2-bad9-b7b93a3e8888'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id, 'MSIClient-{}'.format(test_client_id), self.state1, test_tenant_id)
        consolidated = profile._normalize_properties(test_user, [msi_subscription], True)
        profile._set_subscriptions(consolidated, secondary_key_name='name')

        mock_msi_auth.side_effect = MSRestAzureAuthStub

        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # assert
        self.assertEqual(subscription_id, test_subscription_id)

        # sniff test the msi_auth object
        cred.set_token()
        cred.token
        self.assertTrue(cred.set_token_invoked_count)
        self.assertTrue(cred.token_read_count)
        self.assertTrue(cred.client_id, test_client_id)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    def test_get_login_credentials_msi_user_assigned_with_object_id(self, mock_msi_auth, mock_read_cred_file):
        mock_read_cred_file.return_value = []

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

        mock_msi_auth.side_effect = MSRestAzureAuthStub

        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # assert
        self.assertEqual(subscription_id, test_subscription_id)

        # sniff test the msi_auth object
        cred.set_token()
        cred.token
        self.assertTrue(cred.set_token_invoked_count)
        self.assertTrue(cred.token_read_count)
        self.assertTrue(cred.object_id, test_object_id)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    def test_get_login_credentials_msi_user_assigned_with_res_id(self, mock_msi_auth, mock_read_cred_file):
        mock_read_cred_file.return_value = []

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

        mock_msi_auth.side_effect = MSRestAzureAuthStub

        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # assert
        self.assertEqual(subscription_id, test_subscription_id)

        # sniff test the msi_auth object
        cred.set_token()
        cred.token
        self.assertTrue(cred.set_token_invoked_count)
        self.assertTrue(cred.token_read_count)
        self.assertTrue(cred.msi_res_id, test_res_id)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_raw_token(self, mock_get_token, mock_read_cred_file):
        cli = DummyCli()
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [TestProfile.token_entry1]
        mock_get_token.return_value = (some_token_type, TestProfile.raw_token1,
                                       TestProfile.token_entry1)
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        # action
        creds, sub, tenant = profile.get_raw_token(resource='https://foo')

        # verify
        self.assertEqual(creds[0], self.token_entry1['tokenType'])
        self.assertEqual(creds[1], self.raw_token1)
        # the last in the tuple is the whole token entry which has several fields
        self.assertEqual(creds[2]['expiresOn'], self.token_entry1['expiresOn'])
        mock_get_token.assert_called_once_with(mock.ANY, self.user1, self.tenant_id,
                                               'https://foo')
        self.assertEqual(mock_get_token.call_count, 1)
        self.assertEqual(sub, '1')
        self.assertEqual(tenant, self.tenant_id)

        # Test get_raw_token with tenant
        creds, sub, tenant = profile.get_raw_token(resource='https://foo', tenant=self.tenant_id)

        self.assertEqual(creds[0], self.token_entry1['tokenType'])
        self.assertEqual(creds[1], self.raw_token1)
        self.assertEqual(creds[2]['expiresOn'], self.token_entry1['expiresOn'])
        mock_get_token.assert_called_with(mock.ANY, self.user1, self.tenant_id, 'https://foo')
        self.assertEqual(mock_get_token.call_count, 2)
        self.assertIsNone(sub)
        self.assertEqual(tenant, self.tenant_id)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_service_principal', autospec=True)
    def test_get_raw_token_for_sp(self, mock_get_token, mock_read_cred_file):
        cli = DummyCli()
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [TestProfile.token_entry1]
        mock_get_token.return_value = (some_token_type, TestProfile.raw_token1,
                                       TestProfile.token_entry1)
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties('sp1',
                                                     [self.subscription1],
                                                     True)
        profile._set_subscriptions(consolidated)
        # action
        creds, sub, tenant = profile.get_raw_token(resource='https://foo')

        # verify
        self.assertEqual(creds[0], self.token_entry1['tokenType'])
        self.assertEqual(creds[1], self.raw_token1)
        # the last in the tuple is the whole token entry which has several fields
        self.assertEqual(creds[2]['expiresOn'], self.token_entry1['expiresOn'])
        mock_get_token.assert_called_once_with(mock.ANY, 'sp1', 'https://foo', self.tenant_id, False)
        self.assertEqual(mock_get_token.call_count, 1)
        self.assertEqual(sub, '1')
        self.assertEqual(tenant, self.tenant_id)

        # Test get_raw_token with tenant
        creds, sub, tenant = profile.get_raw_token(resource='https://foo', tenant=self.tenant_id)

        self.assertEqual(creds[0], self.token_entry1['tokenType'])
        self.assertEqual(creds[1], self.raw_token1)
        self.assertEqual(creds[2]['expiresOn'], self.token_entry1['expiresOn'])
        mock_get_token.assert_called_with(mock.ANY, 'sp1', 'https://foo', self.tenant_id, False)
        self.assertEqual(mock_get_token.call_count, 2)
        self.assertIsNone(sub)
        self.assertEqual(tenant, self.tenant_id)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    def test_get_raw_token_msi_system_assigned(self, mock_msi_auth, mock_read_cred_file):
        mock_read_cred_file.return_value = []

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

        mock_msi_auth.side_effect = MSRestAzureAuthStub

        # action
        cred, subscription_id, tenant_id = profile.get_raw_token(resource='http://test_resource')

        # assert
        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(cred[0], 'Bearer')
        self.assertEqual(cred[1], TestProfile.test_msi_access_token)
        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(tenant_id, test_tenant_id)

        # verify tenant shouldn't be specified for MSI account
        with self.assertRaisesRegexp(CLIError, "MSI"):
            cred, subscription_id, _ = profile.get_raw_token(resource='http://test_resource', tenant=self.tenant_id)

    @mock.patch('azure.cli.core._profile.in_cloud_console', autospec=True)
    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    def test_get_raw_token_in_cloud_console(self, mock_msi_auth, mock_read_cred_file, mock_in_cloud_console):
        mock_read_cred_file.return_value = []
        mock_in_cloud_console.return_value = True

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

        mock_msi_auth.side_effect = MSRestAzureAuthStub

        # action
        cred, subscription_id, tenant_id = profile.get_raw_token(resource='http://test_resource')

        # assert
        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(cred[0], 'Bearer')
        self.assertEqual(cred[1], TestProfile.test_msi_access_token)
        self.assertEqual(subscription_id, test_subscription_id)
        self.assertEqual(tenant_id, test_tenant_id)

        # verify tenant shouldn't be specified for Cloud Shell account
        with self.assertRaisesRegexp(CLIError, 'Cloud Shell'):
            cred, subscription_id, _ = profile.get_raw_token(resource='http://test_resource', tenant=self.tenant_id)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_login_credentials_for_graph_client(self, mock_get_token, mock_read_cred_file):
        cli = DummyCli()
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [TestProfile.token_entry1]
        mock_get_token.return_value = (some_token_type, TestProfile.raw_token1)
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1, [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        # action
        cred, _, tenant_id = profile.get_login_credentials(
            resource=cli.cloud.endpoints.active_directory_graph_resource_id)
        _, _ = cred._token_retriever()
        # verify
        mock_get_token.assert_called_once_with(mock.ANY, self.user1, self.tenant_id,
                                               'https://graph.windows.net/')
        self.assertEqual(tenant_id, self.tenant_id)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_login_credentials_for_data_lake_client(self, mock_get_token, mock_read_cred_file):
        cli = DummyCli()
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [TestProfile.token_entry1]
        mock_get_token.return_value = (some_token_type, TestProfile.raw_token1)
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1, [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        # action
        cred, _, tenant_id = profile.get_login_credentials(
            resource=cli.cloud.endpoints.active_directory_data_lake_resource_id)
        _, _ = cred._token_retriever()
        # verify
        mock_get_token.assert_called_once_with(mock.ANY, self.user1, self.tenant_id,
                                               'https://datalake.azure.net/')
        self.assertEqual(tenant_id, self.tenant_id)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.persist_cached_creds', autospec=True)
    def test_logout(self, mock_persist_creds, mock_read_cred_file):
        cli = DummyCli()
        # setup
        mock_read_cred_file.return_value = [TestProfile.token_entry1]

        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        self.assertEqual(1, len(storage_mock['subscriptions']))
        # action
        profile.logout(self.user1)

        # verify
        self.assertEqual(0, len(storage_mock['subscriptions']))
        self.assertEqual(mock_read_cred_file.call_count, 1)
        self.assertEqual(mock_persist_creds.call_count, 1)

    @mock.patch('azure.cli.core._profile._delete_file', autospec=True)
    def test_logout_all(self, mock_delete_cred_file):
        cli = DummyCli()
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
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
        self.assertEqual(mock_delete_cred_file.call_count, 1)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_find_subscriptions_thru_username_password(self, mock_auth_context):
        cli = DummyCli()
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        mock_auth_context.acquire_token.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        mgmt_resource = 'https://management.core.windows.net/'
        # action
        subs = finder.find_from_user_account(self.user1, 'bar', None, mgmt_resource)

        # assert
        self.assertEqual([self.subscription1], subs)
        mock_auth_context.acquire_token_with_username_password.assert_called_once_with(
            mgmt_resource, self.user1, 'bar', mock.ANY)
        mock_auth_context.acquire_token.assert_called_once_with(
            mgmt_resource, self.user1, mock.ANY)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_find_subscriptions_thru_username_non_password(self, mock_auth_context):
        cli = DummyCli()
        mock_auth_context.acquire_token_with_username_password.return_value = None
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: None)
        # action
        subs = finder.find_from_user_account(self.user1, 'bar', None, 'http://goo-resource')

        # assert
        self.assertEqual([], subs)

    @mock.patch('azure.cli.core.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    @mock.patch('azure.cli.core.profiles._shared.get_client_class', autospec=True)
    @mock.patch('azure.cli.core._profile._get_cloud_console_token_endpoint', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder', autospec=True)
    def test_find_subscriptions_in_cloud_console(self, mock_subscription_finder, mock_get_token_endpoint,
                                                 mock_get_client_class, mock_msi_auth):

        class SubscriptionFinderStub:
            def find_from_raw_token(self, tenant, token):
                # make sure the tenant and token args match 'TestProfile.test_msi_access_token'
                if token != TestProfile.test_msi_access_token or tenant != '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a':
                    raise AssertionError('find_from_raw_token was not invoked with expected tenant or token')
                return [TestProfile.subscription1]

        mock_subscription_finder.return_value = SubscriptionFinderStub()

        mock_get_token_endpoint.return_value = "http://great_endpoint"
        mock_msi_auth.return_value = MSRestAzureAuthStub()

        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)

        # action
        subscriptions = profile.find_subscriptions_in_cloud_console()

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'admin3@AzureSDKTeam.onmicrosoft.com')
        self.assertEqual(s['user']['cloudShellID'], True)
        self.assertEqual(s['user']['type'], 'user')
        self.assertEqual(s['name'], self.display_name1)
        self.assertEqual(s['id'], self.id1.split('/')[-1])

    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core.profiles._shared.get_client_class', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_system_assigned(self, mock_get_client_class, mock_get):

        class ClientStub:
            def __init__(self, *args, **kwargs):
                self.subscriptions = mock.MagicMock()
                self.subscriptions.list.return_value = [deepcopy(TestProfile.subscription1_raw)]
                self.config = mock.MagicMock()
                self._client = mock.MagicMock()

        mock_get_client_class.return_value = ClientStub
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        test_token_entry = {
            'token_type': 'Bearer',
            'access_token': TestProfile.test_msi_access_token
        }
        encoded_test_token = json.dumps(test_token_entry).encode()
        good_response = mock.MagicMock()
        good_response.status_code = 200
        good_response.content = encoded_test_token
        mock_get.return_value = good_response

        subscriptions = profile.find_subscriptions_in_vm_with_msi()

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
    @mock.patch('azure.cli.core.profiles._shared.get_client_class', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_no_subscriptions(self, mock_get_client_class, mock_get):

        class ClientStub:
            def __init__(self, *args, **kwargs):
                self.subscriptions = mock.MagicMock()
                self.subscriptions.list.return_value = []
                self.config = mock.MagicMock()
                self._client = mock.MagicMock()

        mock_get_client_class.return_value = ClientStub
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        test_token_entry = {
            'token_type': 'Bearer',
            'access_token': TestProfile.test_msi_access_token
        }
        encoded_test_token = json.dumps(test_token_entry).encode()
        good_response = mock.MagicMock()
        good_response.status_code = 200
        good_response.content = encoded_test_token
        mock_get.return_value = good_response

        subscriptions = profile.find_subscriptions_in_vm_with_msi(allow_no_subscriptions=True)

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'systemAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['user']['assignedIdentityInfo'], 'MSI')
        self.assertEqual(s['name'], 'N/A(tenant level account)')
        self.assertEqual(s['id'], self.test_msi_tenant)
        self.assertEqual(s['tenantId'], self.test_msi_tenant)

    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core.profiles._shared.get_client_class', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_user_assigned_with_client_id(self, mock_get_client_class, mock_get):

        class ClientStub:
            def __init__(self, *args, **kwargs):
                self.subscriptions = mock.MagicMock()
                self.subscriptions.list.return_value = [deepcopy(TestProfile.subscription1_raw)]
                self.config = mock.MagicMock()
                self._client = mock.MagicMock()

        mock_get_client_class.return_value = ClientStub
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

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

        subscriptions = profile.find_subscriptions_in_vm_with_msi(identity_id=test_client_id)

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'userAssignedIdentity')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['name'], self.display_name1)
        self.assertEqual(s['user']['assignedIdentityInfo'], 'MSIClient-{}'.format(test_client_id))
        self.assertEqual(s['id'], self.id1.split('/')[-1])
        self.assertEqual(s['tenantId'], '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a')

    @mock.patch('azure.cli.core.adal_authentication.MSIAuthenticationWrapper', autospec=True)
    @mock.patch('azure.cli.core.profiles._shared.get_client_class', autospec=True)
    @mock.patch('azure.cli.core._profile.SubscriptionFinder', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_user_assigned_with_object_id(self, mock_subscription_finder, mock_get_client_class,
                                                                            mock_msi_auth):
        from requests import HTTPError

        class SubscriptionFinderStub:
            def find_from_raw_token(self, tenant, token):
                # make sure the tenant and token args match 'TestProfile.test_msi_access_token'
                if token != TestProfile.test_msi_access_token or tenant != '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a':
                    raise AssertionError('find_from_raw_token was not invoked with expected tenant or token')
                return [TestProfile.subscription1]

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
                    mock_obj = mock.MagicMock()
                    mock_obj.status, mock_obj.reason = 400, 'Bad Request'
                    raise HTTPError(response=mock_obj)

        profile = Profile(cli_ctx=DummyCli(), storage={'subscriptions': None}, use_global_creds_cache=False,
                          async_persist=False)

        mock_subscription_finder.return_value = SubscriptionFinderStub()

        mock_msi_auth.side_effect = AuthStub
        test_object_id = '54826b22-38d6-4fb2-bad9-b7b93a3e9999'

        # action
        subscriptions = profile.find_subscriptions_in_vm_with_msi(identity_id=test_object_id)

        # assert
        self.assertEqual(subscriptions[0]['user']['assignedIdentityInfo'], 'MSIObject-{}'.format(test_object_id))

    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core.profiles._shared.get_client_class', autospec=True)
    def test_find_subscriptions_in_vm_with_msi_user_assigned_with_res_id(self, mock_get_client_class, mock_get):

        class ClientStub:
            def __init__(self, *args, **kwargs):
                self.subscriptions = mock.MagicMock()
                self.subscriptions.list.return_value = [deepcopy(TestProfile.subscription1_raw)]
                self.config = mock.MagicMock()
                self._client = mock.MagicMock()

        mock_get_client_class.return_value = ClientStub
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

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

        subscriptions = profile.find_subscriptions_in_vm_with_msi(identity_id=test_res_id)

        # assert
        self.assertEqual(subscriptions[0]['user']['assignedIdentityInfo'], 'MSIResource-{}'.format(test_res_id))

    @mock.patch('adal.AuthenticationContext.acquire_token_with_username_password', autospec=True)
    @mock.patch('adal.AuthenticationContext.acquire_token', autospec=True)
    def test_find_subscriptions_thru_username_password_adfs(self, mock_acquire_token,
                                                            mock_acquire_token_username_password):
        cli = DummyCli()
        TEST_ADFS_AUTH_URL = 'https://adfs.local.azurestack.external/adfs'

        def test_acquire_token(self, resource, username, password, client_id):
            global acquire_token_invoked
            acquire_token_invoked = True
            if (self.authority.url == TEST_ADFS_AUTH_URL and self.authority.is_adfs_authority):
                return TestProfile.token_entry1
            else:
                raise ValueError('AuthContext was not initialized correctly for ADFS')

        mock_acquire_token_username_password.side_effect = test_acquire_token
        mock_acquire_token.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        cli.cloud.endpoints.active_directory = TEST_ADFS_AUTH_URL
        finder = SubscriptionFinder(cli, _AUTH_CTX_FACTORY, None, lambda _: mock_arm_client)
        mgmt_resource = 'https://management.core.windows.net/'
        # action
        subs = finder.find_from_user_account(self.user1, 'bar', None, mgmt_resource)

        # assert
        self.assertEqual([self.subscription1], subs)
        self.assertTrue(acquire_token_invoked)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    @mock.patch('azure.cli.core._profile.logger', autospec=True)
    def test_find_subscriptions_thru_username_password_with_account_disabled(self, mock_logger, mock_auth_context):
        cli = DummyCli()
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        mock_auth_context.acquire_token.side_effect = AdalError('Account is disabled')
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        mgmt_resource = 'https://management.core.windows.net/'
        # action
        subs = finder.find_from_user_account(self.user1, 'bar', None, mgmt_resource)

        # assert
        self.assertEqual([], subs)
        mock_logger.warning.assert_called_once_with(mock.ANY, mock.ANY, mock.ANY)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_find_subscriptions_from_particular_tenent(self, mock_auth_context):
        def just_raise(ex):
            raise ex

        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.side_effect = lambda: just_raise(
            ValueError("'tenants.list' should not occur"))
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        # action
        subs = finder.find_from_user_account(self.user1, 'bar', self.tenant_id, 'http://someresource')

        # assert
        self.assertEqual([self.subscription1], subs)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_find_subscriptions_through_device_code_flow(self, mock_auth_context):
        cli = DummyCli()
        test_nonsense_code = {'message': 'magic code for you'}
        mock_auth_context.acquire_user_code.return_value = test_nonsense_code
        mock_auth_context.acquire_token_with_device_code.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        mgmt_resource = 'https://management.core.windows.net/'
        # action
        subs = finder.find_through_interactive_flow(None, mgmt_resource)

        # assert
        self.assertEqual([self.subscription1], subs)
        mock_auth_context.acquire_user_code.assert_called_once_with(
            mgmt_resource, mock.ANY)
        mock_auth_context.acquire_token_with_device_code.assert_called_once_with(
            mgmt_resource, test_nonsense_code, mock.ANY)
        mock_auth_context.acquire_token.assert_called_once_with(
            mgmt_resource, self.user1, mock.ANY)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    @mock.patch('azure.cli.core._profile._get_authorization_code', autospec=True)
    def test_find_subscriptions_through_authorization_code_flow(self, _get_authorization_code_mock, mock_auth_context):
        import adal
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        token_cache = adal.TokenCache()
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, token_cache, lambda _: mock_arm_client)
        _get_authorization_code_mock.return_value = {
            'code': 'code1',
            'reply_url': 'http://localhost:8888'
        }
        mgmt_resource = 'https://management.core.windows.net/'
        temp_token_cache = mock.MagicMock()
        type(mock_auth_context).cache = temp_token_cache
        temp_token_cache.read_items.return_value = []
        mock_auth_context.acquire_token_with_authorization_code.return_value = self.token_entry1

        # action
        subs = finder.find_through_authorization_code_flow(None, mgmt_resource, 'https:/some_aad_point/common')

        # assert
        self.assertEqual([self.subscription1], subs)
        mock_auth_context.acquire_token.assert_called_once_with(mgmt_resource, self.user1, mock.ANY)
        mock_auth_context.acquire_token_with_authorization_code.assert_called_once_with('code1',
                                                                                        'http://localhost:8888',
                                                                                        mgmt_resource, mock.ANY,
                                                                                        None)
        _get_authorization_code_mock.assert_called_once_with(mgmt_resource, 'https:/some_aad_point/common')

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_find_subscriptions_interactive_from_particular_tenent(self, mock_auth_context):
        def just_raise(ex):
            raise ex

        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.side_effect = lambda: just_raise(
            ValueError("'tenants.list' should not occur"))
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        # action
        subs = finder.find_through_interactive_flow(self.tenant_id, 'http://someresource')

        # assert
        self.assertEqual([self.subscription1], subs)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_find_subscriptions_from_service_principal_id(self, mock_auth_context):
        cli = DummyCli()
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        mgmt_resource = 'https://management.core.windows.net/'
        # action
        subs = finder.find_from_service_principal_id('my app', ServicePrincipalAuth('my secret'),
                                                     self.tenant_id, mgmt_resource)

        # assert
        self.assertEqual([self.subscription1], subs)
        mock_arm_client.tenants.list.assert_not_called()
        mock_auth_context.acquire_token.assert_not_called()
        mock_auth_context.acquire_token_with_client_credentials.assert_called_once_with(
            mgmt_resource, 'my app', 'my secret')

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_find_subscriptions_from_service_principal_using_cert(self, mock_auth_context):
        cli = DummyCli()
        mock_auth_context.acquire_token_with_client_certificate.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        mgmt_resource = 'https://management.core.windows.net/'

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')

        # action
        subs = finder.find_from_service_principal_id('my app', ServicePrincipalAuth(test_cert_file),
                                                     self.tenant_id, mgmt_resource)

        # assert
        self.assertEqual([self.subscription1], subs)
        mock_arm_client.tenants.list.assert_not_called()
        mock_auth_context.acquire_token.assert_not_called()
        mock_auth_context.acquire_token_with_client_certificate.assert_called_once_with(
            mgmt_resource, 'my app', mock.ANY, mock.ANY, None)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_find_subscriptions_from_service_principal_using_cert_sn_issuer(self, mock_auth_context):
        cli = DummyCli()
        mock_auth_context.acquire_token_with_client_certificate.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [deepcopy(self.subscription1_raw)]
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        mgmt_resource = 'https://management.core.windows.net/'

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')
        with open(test_cert_file) as cert_file:
            cert_file_string = cert_file.read()
        match = re.search(r'\-+BEGIN CERTIFICATE.+\-+(?P<public>[^-]+)\-+END CERTIFICATE.+\-+',
                          cert_file_string, re.I)
        public_certificate = match.group('public').strip()
        # action
        subs = finder.find_from_service_principal_id('my app', ServicePrincipalAuth(test_cert_file, use_cert_sn_issuer=True),
                                                     self.tenant_id, mgmt_resource)

        # assert
        self.assertEqual([self.subscription1], subs)
        mock_arm_client.tenants.list.assert_not_called()
        mock_auth_context.acquire_token.assert_not_called()
        mock_auth_context.acquire_token_with_client_certificate.assert_called_once_with(
            mgmt_resource, 'my app', mock.ANY, mock.ANY, public_certificate)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_refresh_accounts_one_user_account(self, mock_auth_context):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False)
        profile._set_subscriptions(consolidated)
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        mock_auth_context.acquire_token.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = deepcopy([self.subscription1_raw, self.subscription2_raw])
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        # action
        profile.refresh_accounts(finder)

        # assert
        result = storage_mock['subscriptions']
        self.assertEqual(2, len(result))
        self.assertEqual(self.id1.split('/')[-1], result[0]['id'])
        self.assertEqual(self.id2.split('/')[-1], result[1]['id'])
        self.assertTrue(result[0]['isDefault'])

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_refresh_accounts_one_user_account_one_sp_account(self, mock_auth_context):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        sp_subscription1 = SubscriptionStub('sp-sub/3', 'foo-subname', self.state1, 'foo_tenant.onmicrosoft.com')
        consolidated = profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False)
        consolidated += profile._normalize_properties('http://foo', [sp_subscription1], True)
        profile._set_subscriptions(consolidated)
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        mock_auth_context.acquire_token.return_value = self.token_entry1
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.side_effect = deepcopy([[self.subscription1], [self.subscription2, sp_subscription1]])
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        profile._creds_cache.retrieve_secret_of_service_principal = lambda _: 'verySecret'
        profile._creds_cache.flush_to_disk = lambda _: ''
        # action
        profile.refresh_accounts(finder)

        # assert
        result = storage_mock['subscriptions']
        self.assertEqual(3, len(result))
        self.assertEqual(self.id1.split('/')[-1], result[0]['id'])
        self.assertEqual(self.id2.split('/')[-1], result[1]['id'])
        self.assertEqual('3', result[2]['id'])
        self.assertTrue(result[0]['isDefault'])

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_refresh_accounts_with_nothing(self, mock_auth_context):
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)
        consolidated = profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False)
        profile._set_subscriptions(consolidated)
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        mock_auth_context.acquire_token.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = []
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, None, lambda _: mock_arm_client)
        # action
        profile.refresh_accounts(finder)

        # assert
        result = storage_mock['subscriptions']
        self.assertEqual(0, len(result))

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_credscache_load_tokens_and_sp_creds_with_secret(self, mock_read_file):
        cli = DummyCli()
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_read_file.return_value = [self.token_entry1, test_sp]

        # action
        creds_cache = CredsCache(cli, async_persist=False)

        # assert
        token_entries = [entry for _, entry in creds_cache.load_adal_token_cache().read_items()]
        self.assertEqual(token_entries, [self.token_entry1])
        self.assertEqual(creds_cache._service_principal_creds, [test_sp])

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_credscache_load_tokens_and_sp_creds_with_cert(self, mock_read_file):
        cli = DummyCli()
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "certificateFile": 'junkcert.pem'
        }
        mock_read_file.return_value = [test_sp]

        # action
        creds_cache = CredsCache(cli, async_persist=False)
        creds_cache.load_adal_token_cache()

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [test_sp])

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_credscache_retrieve_sp_secret_with_cert(self, mock_read_file):
        cli = DummyCli()
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "certificateFile": 'junkcert.pem'
        }
        mock_read_file.return_value = [test_sp]

        # action
        creds_cache = CredsCache(cli, async_persist=False)
        creds_cache.load_adal_token_cache()

        # assert
        self.assertEqual(creds_cache.retrieve_secret_of_service_principal(test_sp['servicePrincipalId']), None)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('os.fdopen', autospec=True)
    @mock.patch('os.open', autospec=True)
    def test_credscache_add_new_sp_creds(self, _, mock_open_for_write, mock_read_file):
        cli = DummyCli()
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
        mock_open_for_write.return_value = FileHandleStub()
        mock_read_file.return_value = [self.token_entry1, test_sp]
        creds_cache = CredsCache(cli, async_persist=False)

        # action
        creds_cache.save_service_principal_cred(test_sp2)

        # assert
        token_entries = [e for _, e in creds_cache.adal_token_cache.read_items()]  # noqa: F812
        self.assertEqual(token_entries, [self.token_entry1])
        self.assertEqual(creds_cache._service_principal_creds, [test_sp, test_sp2])
        mock_open_for_write.assert_called_with(mock.ANY, 'w+')

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('os.fdopen', autospec=True)
    @mock.patch('os.open', autospec=True)
    def test_credscache_add_preexisting_sp_creds(self, _, mock_open_for_write, mock_read_file):
        cli = DummyCli()
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write.return_value = FileHandleStub()
        mock_read_file.return_value = [test_sp]
        creds_cache = CredsCache(cli, async_persist=False)

        # action
        creds_cache.save_service_principal_cred(test_sp)

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [test_sp])
        self.assertFalse(mock_open_for_write.called)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('os.fdopen', autospec=True)
    @mock.patch('os.open', autospec=True)
    def test_credscache_add_preexisting_sp_new_secret(self, _, mock_open_for_write, mock_read_file):
        cli = DummyCli()
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write.return_value = FileHandleStub()
        mock_read_file.return_value = [test_sp]
        creds_cache = CredsCache(cli, async_persist=False)

        new_creds = test_sp.copy()
        new_creds['accessToken'] = 'Secret2'
        # action
        creds_cache.save_service_principal_cred(new_creds)

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [new_creds])
        self.assertTrue(mock_open_for_write.called)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('os.fdopen', autospec=True)
    @mock.patch('os.open', autospec=True)
    def test_credscache_match_service_principal_correctly(self, _, mock_open_for_write, mock_read_file):
        cli = DummyCli()
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write.return_value = FileHandleStub()
        mock_read_file.return_value = [test_sp]
        factory = mock.MagicMock()
        factory.side_effect = ValueError('SP was found')
        creds_cache = CredsCache(cli, factory, async_persist=False)

        # action and verify(we plant an exception to throw after the SP was found; so if the exception is thrown,
        # we know the matching did go through)
        self.assertRaises(ValueError, creds_cache.retrieve_token_for_service_principal,
                          'myapp', 'resource1', 'mytenant', False)

        # tenant doesn't exactly match, but it still succeeds
        # before fully migrating to pytest and utilizing capsys fixture, use `pytest -o log_cli=True` to manually
        # verify the warning log
        self.assertRaises(ValueError, creds_cache.retrieve_token_for_service_principal,
                          'myapp', 'resource1', 'mytenant2', False)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('os.fdopen', autospec=True)
    @mock.patch('os.open', autospec=True)
    def test_credscache_remove_creds(self, _, mock_open_for_write, mock_read_file):
        cli = DummyCli()
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write.return_value = FileHandleStub()
        mock_read_file.return_value = [self.token_entry1, test_sp]
        creds_cache = CredsCache(cli, async_persist=False)

        # action #1, logout a user
        creds_cache.remove_cached_creds(self.user1)

        # assert #1
        token_entries = [e for _, e in creds_cache.adal_token_cache.read_items()]  # noqa: F812
        self.assertEqual(token_entries, [])

        # action #2 logout a service principal
        creds_cache.remove_cached_creds('myapp')

        # assert #2
        self.assertEqual(creds_cache._service_principal_creds, [])

        mock_open_for_write.assert_called_with(mock.ANY, 'w+')
        self.assertEqual(mock_open_for_write.call_count, 2)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('os.fdopen', autospec=True)
    @mock.patch('os.open', autospec=True)
    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_credscache_new_token_added_by_adal(self, mock_adal_auth_context, _, mock_open_for_write, mock_read_file):  # pylint: disable=line-too-long
        cli = DummyCli()
        token_entry2 = {
            "accessToken": "new token",
            "tokenType": "Bearer",
            "userId": self.user1
        }

        def acquire_token_side_effect(*args):  # pylint: disable=unused-argument
            creds_cache.adal_token_cache.has_state_changed = True
            return token_entry2

        def get_auth_context(_, authority, **kwargs):  # pylint: disable=unused-argument
            mock_adal_auth_context.cache = kwargs['cache']
            return mock_adal_auth_context

        mock_adal_auth_context.acquire_token.side_effect = acquire_token_side_effect
        mock_open_for_write.return_value = FileHandleStub()
        mock_read_file.return_value = [self.token_entry1]
        creds_cache = CredsCache(cli, auth_ctx_factory=get_auth_context, async_persist=False)

        # action
        mgmt_resource = 'https://management.core.windows.net/'
        token_type, token, _ = creds_cache.retrieve_token_for_user(self.user1, self.tenant_id,
                                                                   mgmt_resource)
        mock_adal_auth_context.acquire_token.assert_called_once_with(
            'https://management.core.windows.net/',
            self.user1,
            mock.ANY)

        # assert
        mock_open_for_write.assert_called_with(mock.ANY, 'w+')
        self.assertEqual(token, 'new token')
        self.assertEqual(token_type, token_entry2['tokenType'])

    @mock.patch('azure.cli.core._profile.get_file_json', autospec=True)
    def test_credscache_good_error_on_file_corruption(self, mock_read_file):
        mock_read_file.side_effect = ValueError('a bad error for you')
        cli = DummyCli()

        # action
        creds_cache = CredsCache(cli, async_persist=False)

        # assert
        with self.assertRaises(CLIError) as context:
            creds_cache.load_adal_token_cache()

        self.assertTrue(re.findall(r'bad error for you', str(context.exception)))

    def test_service_principal_auth_client_secret(self):
        sp_auth = ServicePrincipalAuth('verySecret!')
        result = sp_auth.get_entry_to_persist('sp_id1', 'tenant1')
        self.assertEqual(result, {
            'servicePrincipalId': 'sp_id1',
            'servicePrincipalTenant': 'tenant1',
            'accessToken': 'verySecret!'
        })

    def test_service_principal_auth_client_cert(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')
        sp_auth = ServicePrincipalAuth(test_cert_file)

        result = sp_auth.get_entry_to_persist('sp_id1', 'tenant1')
        self.assertEqual(result, {
            'servicePrincipalId': 'sp_id1',
            'servicePrincipalTenant': 'tenant1',
            'certificateFile': test_cert_file,
            'thumbprint': 'F0:6A:53:84:8B:BE:71:4A:42:90:D6:9D:33:52:79:C1:D0:10:73:FD'
        })

    def test_detect_adfs_authority_url(self):
        cli = DummyCli()
        adfs_url_1 = 'https://adfs.redmond.ext-u15f2402.masd.stbtest.microsoft.com/adfs/'
        cli.cloud.endpoints.active_directory = adfs_url_1
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        # test w/ trailing slash
        r = profile.auth_ctx_factory(cli, 'common', None)
        self.assertEqual(r.authority.url, adfs_url_1.rstrip('/'))

        # test w/o trailing slash
        adfs_url_2 = 'https://adfs.redmond.ext-u15f2402.masd.stbtest.microsoft.com/adfs'
        cli.cloud.endpoints.active_directory = adfs_url_2
        r = profile.auth_ctx_factory(cli, 'common', None)
        self.assertEqual(r.authority.url, adfs_url_2)

        # test w/ regular aad
        aad_url = 'https://login.microsoftonline.com'
        cli.cloud.endpoints.active_directory = aad_url
        r = profile.auth_ctx_factory(cli, 'common', None)
        self.assertEqual(r.authority.url, aad_url + '/common')

    @mock.patch('adal.AuthenticationContext', autospec=True)
    @mock.patch('azure.cli.core._profile._get_authorization_code', autospec=True)
    def test_find_using_common_tenant(self, _get_authorization_code_mock, mock_auth_context):
        """When a subscription can be listed by multiple tenants, only the first appearance is retained
        """
        import adal
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        tenant2 = "00000002-0000-0000-0000-000000000000"
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id), TenantStub(tenant2)]

        # same subscription but listed from another tenant
        subscription2_raw = SubscriptionStub(self.id1, self.display_name1, self.state1, self.tenant_id)
        mock_arm_client.subscriptions.list.side_effect = [[deepcopy(self.subscription1_raw)], [subscription2_raw]]

        mgmt_resource = 'https://management.core.windows.net/'
        token_cache = adal.TokenCache()
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, token_cache, lambda _: mock_arm_client)
        all_subscriptions = finder._find_using_common_tenant(access_token="token1", resource=mgmt_resource)

        self.assertEqual(len(all_subscriptions), 1)
        self.assertEqual(all_subscriptions[0].tenant_id, self.tenant_id)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    @mock.patch('azure.cli.core._profile._get_authorization_code', autospec=True)
    def test_find_using_common_tenant_mfa_warning(self, _get_authorization_code_mock, mock_auth_context):
        # Assume 2 tenants. Home tenant tenant1 doesn't require MFA, but tenant2 does
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
        all_subscriptions = finder._find_using_common_tenant(access_token="token1",
                                                             resource='https://management.core.windows.net/')

        # assert
        # subscriptions are correctly returned
        self.assertEqual(all_subscriptions, [self.subscription1])
        self.assertEqual(mock_auth_context.acquire_token.call_count, 2)

        # With pytest, use -o log_cli=True to manually check the log

    @mock.patch('adal.AuthenticationContext', autospec=True)
    @mock.patch('azure.cli.core._profile._get_authorization_code', autospec=True)
    def test_find_using_specific_tenant(self, _get_authorization_code_mock, mock_auth_context):
        """ Test tenant_id -> home_tenant_id mapping and token tenant attachment
        """
        import adal
        cli = DummyCli()
        mock_arm_client = mock.MagicMock()
        token_tenant = "00000001-0000-0000-0000-000000000000"
        home_tenant = "00000002-0000-0000-0000-000000000000"

        subscription_raw = SubscriptionStub(self.id1, self.display_name1, self.state1, tenant_id=home_tenant)
        mock_arm_client.subscriptions.list.return_value = [subscription_raw]

        token_cache = adal.TokenCache()
        finder = SubscriptionFinder(cli, lambda _, _1, _2: mock_auth_context, token_cache, lambda _: mock_arm_client)
        all_subscriptions = finder._find_using_specific_tenant(tenant=token_tenant, access_token="token1")

        self.assertEqual(len(all_subscriptions), 1)
        self.assertEqual(all_subscriptions[0].tenant_id, token_tenant)
        self.assertEqual(all_subscriptions[0].home_tenant_id, home_tenant)

    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    @mock.patch('azure.cli.core._msal.AdalRefreshTokenBasedClientApplication._acquire_token_silent_by_finding_specific_refresh_token', autospec=True)
    def test_get_msal_token(self, mock_acquire_token, mock_retrieve_token_for_user):
        """
        This is added only for vmssh feature.
        It is a temporary solution and will deprecate after MSAL adopted completely.
        """
        cli = DummyCli()
        storage_mock = {'subscriptions': None}
        profile = Profile(cli_ctx=cli, storage=storage_mock, use_global_creds_cache=False, async_persist=False)

        consolidated = profile._normalize_properties(self.user1, [self.subscription1], False)
        profile._set_subscriptions(consolidated)

        some_token_type = 'Bearer'
        mock_retrieve_token_for_user.return_value = (some_token_type, TestProfile.raw_token1, TestProfile.token_entry1)
        mock_acquire_token.return_value = {
            'access_token': 'fake_access_token'
        }
        scopes = ["https://pas.windows.net/CheckMyAccess/Linux/user_impersonation"]
        data = {
            "token_type": "ssh-cert",
            "req_cnf": "fake_jwk",
            "key_id": "fake_id"
        }
        username, access_token = profile.get_msal_token(scopes, data)
        self.assertEqual(username, self.user1)
        self.assertEqual(access_token, 'fake_access_token')


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
        super(SubscriptionStub, self).__init__(subscription_policies=policies, authorization_source='some_authorization_source')
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


if __name__ == '__main__':
    unittest.main()
