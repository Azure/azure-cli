# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, unsubscriptable-object
import json
import os
import unittest
import mock

from adal import AdalError
from azure.mgmt.resource.subscriptions.models import (SubscriptionState, Subscription,
                                                      SubscriptionPolicies, SpendingLimit)
from azure.cli.core._profile import (Profile, CredsCache, SubscriptionFinder,
                                     ServicePrincipalAuth, CLOUD)
from azure.cli.core.util import CLIError


class Test_Profile(unittest.TestCase):  # pylint: disable=too-many-public-methods

    @classmethod
    def setUpClass(cls):
        cls.tenant_id = 'microsoft.com'
        cls.user1 = 'foo@foo.com'
        cls.id1 = 'subscriptions/1'
        cls.display_name1 = 'foo account'
        cls.state1 = SubscriptionState.enabled
        cls.subscription1 = SubscriptionStub(cls.id1,
                                             cls.display_name1,
                                             cls.state1,
                                             cls.tenant_id)
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
        cls.subscription2 = SubscriptionStub(cls.id2,
                                             cls.display_name2,
                                             cls.state2,
                                             cls.tenant_id)

    def test_normalize(self):
        consolidated = Profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        expected = {
            'environmentName': 'AzureCloud',
            'id': '1',
            'name': self.display_name1,
            'state': self.state1.value,
            'user': {
                'name': self.user1,
                'type': 'user'
            },
            'isDefault': False,
            'tenantId': self.tenant_id
        }
        self.assertEqual(expected, consolidated[0])
        # verify serialization works
        self.assertIsNotNone(json.dumps(consolidated[0]))

    def test_update_add_two_different_subscriptions(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        # add the first and verify
        consolidated = Profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)

        self.assertEqual(len(storage_mock['subscriptions']), 1)
        subscription1 = storage_mock['subscriptions'][0]
        self.assertEqual(subscription1, {
            'environmentName': 'AzureCloud',
            'id': '1',
            'name': self.display_name1,
            'state': self.state1.value,
            'user': {
                'name': self.user1,
                'type': 'user'
            },
            'isDefault': True,
            'tenantId': self.tenant_id
        })

        # add the second and verify
        consolidated = Profile._normalize_properties(self.user2,
                                                     [self.subscription2],
                                                     False)
        profile._set_subscriptions(consolidated)

        self.assertEqual(len(storage_mock['subscriptions']), 2)
        subscription2 = storage_mock['subscriptions'][1]
        self.assertEqual(subscription2, {
            'environmentName': 'AzureCloud',
            'id': '2',
            'name': self.display_name2,
            'state': self.state2.value,
            'user': {
                'name': self.user2,
                'type': 'user'
            },
            'isDefault': True,
            'tenantId': self.tenant_id
        })

        # verify the old one stays, but no longer active
        self.assertEqual(storage_mock['subscriptions'][0]['name'],
                         subscription1['name'])
        self.assertFalse(storage_mock['subscriptions'][0]['isDefault'])

    def test_update_with_same_subscription_added_twice(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        # add one twice and verify we will have one but with new token
        consolidated = Profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)

        new_subscription1 = SubscriptionStub(self.id1,
                                             self.display_name1,
                                             self.state1,
                                             self.tenant_id)
        consolidated = Profile._normalize_properties(self.user1,
                                                     [new_subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)

        self.assertEqual(len(storage_mock['subscriptions']), 1)
        self.assertTrue(storage_mock['subscriptions'][0]['isDefault'])

    def test_set_active_subscription(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        consolidated = Profile._normalize_properties(self.user1,
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
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        subscriptions = profile._normalize_properties(
            self.user2, [self.subscription2, self.subscription1], False)

        profile._set_subscriptions(subscriptions)

        # verify we skip the overdued subscription and default to the 2nd one in the list
        self.assertEqual(storage_mock['subscriptions'][1]['name'], self.subscription1.display_name)
        self.assertTrue(storage_mock['subscriptions'][1]['isDefault'])

    def test_get_subscription(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        consolidated = Profile._normalize_properties(self.user1,
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

    def test_get_expanded_subscription_info(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        consolidated = Profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        sub_id = self.id1.split('/')[-1]

        # testing dump of existing logged in account
        extended_info = profile.get_expanded_subscription_info()
        self.assertEqual(self.user1, extended_info['userName'])
        self.assertEqual(sub_id, extended_info['subscriptionId'])
        self.assertEqual(self.display_name1, extended_info['subscriptionName'])
        self.assertEqual('https://login.microsoftonline.com',
                         extended_info['endpoints'].active_directory)

        # testing dump of service principal by 'create-for-rbac'
        extended_info = profile.get_expanded_subscription_info(name='great-sp',
                                                               password='verySecret-')
        self.assertEqual(sub_id, extended_info['subscriptionId'])
        self.assertEqual(self.display_name1, extended_info['subscriptionName'])
        self.assertEqual('great-sp', extended_info['client'])
        self.assertEqual('https://login.microsoftonline.com',
                         extended_info['endpoints'].active_directory)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_get_expanded_subscription_info_for_logged_in_service_principal(self,
                                                                            mock_auth_context):
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [self.subscription1]
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(storage_mock)
        profile._management_resource_uri = 'https://management.core.windows.net/'
        profile.find_subscriptions_on_login(False,
                                            '1234',
                                            'my-secret',
                                            True,
                                            self.tenant_id,
                                            False,
                                            finder)
        # action
        extended_info = profile.get_expanded_subscription_info()
        # assert
        self.assertEqual(self.id1.split('/')[-1], extended_info['subscriptionId'])
        self.assertEqual(self.display_name1, extended_info['subscriptionName'])
        self.assertEqual('1234', extended_info['client'])
        self.assertEqual('https://login.microsoftonline.com',
                         extended_info['endpoints'].active_directory)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_create_account_without_subscriptions(self, mock_auth_context):
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = []
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(storage_mock)
        profile._management_resource_uri = 'https://management.core.windows.net/'

        # action
        result = profile.find_subscriptions_on_login(False,
                                                     '1234',
                                                     'my-secret',
                                                     True,
                                                     self.tenant_id,
                                                     allow_no_subscriptions=True,
                                                     subscription_finder=finder)

        # assert
        self.assertTrue(1, len(result))
        self.assertEqual(result[0]['id'], self.tenant_id)
        self.assertEqual(result[0]['state'], 'Enabled')
        self.assertEqual(result[0]['tenantId'], self.tenant_id)
        self.assertEqual(result[0]['name'], 'N/A(tenant level account)')

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_create_account_without_subscriptions_without_tenant(self, mock_auth_context):
        finder = mock.MagicMock()
        finder.find_through_interactive_flow.return_value = []
        storage_mock = {'subscriptions': []}
        profile = Profile(storage_mock)

        # action
        result = profile.find_subscriptions_on_login(True,
                                                     '1234',
                                                     'my-secret',
                                                     False,
                                                     None,
                                                     allow_no_subscriptions=True,
                                                     subscription_finder=finder)

        # assert
        self.assertTrue(0 == len(result))

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_get_current_account_user(self, mock_read_cred_file):
        # setup
        mock_read_cred_file.return_value = [Test_Profile.token_entry1]

        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)
        consolidated = Profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        # action
        user = profile.get_current_account_user()

        # verify
        self.assertEqual(user, self.user1)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', return_value=None)
    def test_create_token_cache(self, mock_read_file):
        mock_read_file.return_value = []
        profile = Profile()
        cache = profile._creds_cache.adal_token_cache
        self.assertFalse(cache.read_items())
        self.assertTrue(mock_read_file.called)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_load_cached_tokens(self, mock_read_file):
        mock_read_file.return_value = [Test_Profile.token_entry1]
        profile = Profile()
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
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [Test_Profile.token_entry1]
        mock_get_token.return_value = (some_token_type, Test_Profile.raw_token1)
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)
        consolidated = Profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # verify
        self.assertEqual(subscription_id, '1')

        # verify the cred._tokenRetriever is a working lambda
        token_type, token = cred._token_retriever()
        self.assertEqual(token, self.raw_token1)
        self.assertEqual(some_token_type, token_type)
        mock_get_token.assert_called_once_with(mock.ANY, self.user1, self.tenant_id,
                                               'https://management.core.windows.net/')
        self.assertEqual(mock_get_token.call_count, 1)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_login_credentials_for_graph_client(self, mock_get_token, mock_read_cred_file):
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [Test_Profile.token_entry1]
        mock_get_token.return_value = (some_token_type, Test_Profile.raw_token1)
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)
        consolidated = Profile._normalize_properties(self.user1, [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        # action
        cred, _, tenant_id = profile.get_login_credentials(
            resource=CLOUD.endpoints.active_directory_graph_resource_id)
        _, _ = cred._token_retriever()
        # verify
        mock_get_token.assert_called_once_with(mock.ANY, self.user1, self.tenant_id,
                                               'https://graph.windows.net/')
        self.assertEqual(tenant_id, self.tenant_id)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.persist_cached_creds', autospec=True)
    def test_logout(self, mock_persist_creds, mock_read_cred_file):
        # setup
        mock_read_cred_file.return_value = [Test_Profile.token_entry1]

        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)
        consolidated = Profile._normalize_properties(self.user1,
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
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)
        consolidated = Profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        consolidated2 = Profile._normalize_properties(self.user2,
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
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        mock_auth_context.acquire_token.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [self.subscription1]
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)
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
    @mock.patch('azure.cli.core._profile.logger', autospec=True)
    def test_find_subscriptions_thru_username_password_with_account_disabled(self, mock_logger,
                                                                             mock_auth_context):
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        mock_auth_context.acquire_token.side_effect = AdalError('Account is disabled')
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)
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

        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.side_effect = lambda: just_raise(
            ValueError("'tenants.list' should not occur"))
        mock_arm_client.subscriptions.list.return_value = [self.subscription1]
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)
        # action
        subs = finder.find_from_user_account(self.user1, 'bar', 'NiceTenant', 'http://someresource')

        # assert
        self.assertEqual([self.subscription1], subs)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_find_subscriptions_through_interactive_flow(self, mock_auth_context):
        test_nonsense_code = {'message': 'magic code for you'}
        mock_auth_context.acquire_user_code.return_value = test_nonsense_code
        mock_auth_context.acquire_token_with_device_code.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [self.subscription1]
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)
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
    def test_find_subscriptions_interactive_from_particular_tenent(self, mock_auth_context):
        def just_raise(ex):
            raise ex

        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.side_effect = lambda: just_raise(
            ValueError("'tenants.list' should not occur"))
        mock_arm_client.subscriptions.list.return_value = [self.subscription1]
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)
        # action
        subs = finder.find_through_interactive_flow('NiceTenant', 'http://someresource')

        # assert
        self.assertEqual([self.subscription1], subs)

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_find_subscriptions_from_service_principal_id(self, mock_auth_context):
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [self.subscription1]
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)
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
        mock_auth_context.acquire_token_with_client_certificate.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [self.subscription1]
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)
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
            mgmt_resource, 'my app', mock.ANY, mock.ANY)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_credscache_load_tokens_and_sp_creds_with_secret(self, mock_read_file):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_read_file.return_value = [self.token_entry1, test_sp]

        # action
        creds_cache = CredsCache()

        # assert
        token_entries = [entry for _, entry in creds_cache.load_adal_token_cache().read_items()]
        self.assertEqual(token_entries, [self.token_entry1])
        self.assertEqual(creds_cache._service_principal_creds, [test_sp])

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_credscache_load_tokens_and_sp_creds_with_cert(self, mock_read_file):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "certificateFile": 'junkcert.pem'
        }
        mock_read_file.return_value = [test_sp]

        # action
        creds_cache = CredsCache()
        creds_cache.load_adal_token_cache()

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [test_sp])

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('os.fdopen', autospec=True)
    @mock.patch('os.open', autospec=True)
    def test_credscache_add_new_sp_creds(self, _, mock_open_for_write, mock_read_file):
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
        creds_cache = CredsCache()

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
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write.return_value = FileHandleStub()
        mock_read_file.return_value = [test_sp]
        creds_cache = CredsCache()

        # action
        creds_cache.save_service_principal_cred(test_sp)

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [test_sp])

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('os.fdopen', autospec=True)
    @mock.patch('os.open', autospec=True)
    def test_credscache_remove_creds(self, _, mock_open_for_write, mock_read_file):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write.return_value = FileHandleStub()
        mock_read_file.return_value = [self.token_entry1, test_sp]
        creds_cache = CredsCache()

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
        token_entry2 = {
            "accessToken": "new token",
            "tokenType": "Bearer",
            "userId": self.user1
        }

        def acquire_token_side_effect(*args):  # pylint: disable=unused-argument
            creds_cache.adal_token_cache.has_state_changed = True
            return token_entry2

        def get_auth_context(authority, **kwargs):  # pylint: disable=unused-argument
            mock_adal_auth_context.cache = kwargs['cache']
            return mock_adal_auth_context

        mock_adal_auth_context.acquire_token.side_effect = acquire_token_side_effect
        mock_open_for_write.return_value = FileHandleStub()
        mock_read_file.return_value = [self.token_entry1]
        creds_cache = CredsCache(auth_ctx_factory=get_auth_context)

        # action
        mgmt_resource = 'https://management.core.windows.net/'
        token_type, token = creds_cache.retrieve_token_for_user(self.user1, self.tenant_id,
                                                                mgmt_resource)
        mock_adal_auth_context.acquire_token.assert_called_once_with(
            'https://management.core.windows.net/',
            self.user1,
            mock.ANY)

        # assert
        mock_open_for_write.assert_called_with(mock.ANY, 'w+')
        self.assertEqual(token, 'new token')
        self.assertEqual(token_type, token_entry2['tokenType'])

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


class FileHandleStub(object):  # pylint: disable=too-few-public-methods

    def write(self, content):
        pass

    def __enter__(self):
        return self

    def __exit__(self, _2, _3, _4):
        pass


class SubscriptionStub(Subscription):  # pylint: disable=too-few-public-methods

    def __init__(self, id, display_name, state, tenant_id):  # pylint: disable=redefined-builtin,
        policies = SubscriptionPolicies()
        policies.spending_limit = SpendingLimit.current_period_off
        policies.quota_id = 'some quota'
        super(SubscriptionStub, self).__init__(policies, 'some_authorization_source')
        self.id = id
        self.display_name = display_name
        self.state = state
        self.tenant_id = tenant_id


class TenantStub(object):  # pylint: disable=too-few-public-methods

    def __init__(self, tenant_id):
        self.tenant_id = tenant_id


if __name__ == '__main__':
    unittest.main()
