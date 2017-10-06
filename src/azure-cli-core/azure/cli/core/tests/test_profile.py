# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
import json
import os
import unittest
import mock

from copy import deepcopy

from adal import AdalError
from azure.mgmt.resource.subscriptions.models import (SubscriptionState, Subscription,
                                                      SubscriptionPolicies, SpendingLimit)
from azure.cli.core._profile import (Profile, CredsCache, SubscriptionFinder,
                                     ServicePrincipalAuth, CLOUD, _AUTH_CTX_FACTORY)
from azure.cli.core.util import CLIError


class Test_Profile(unittest.TestCase):

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
        profile = Profile(storage_mock, use_global_creds_cache=False)

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
        profile = Profile(storage_mock, use_global_creds_cache=False)

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
        profile = Profile(storage_mock, use_global_creds_cache=False)

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
        profile = Profile(storage_mock, use_global_creds_cache=False)

        subscriptions = profile._normalize_properties(
            self.user2, [self.subscription2, self.subscription1], False)

        profile._set_subscriptions(subscriptions)

        # verify we skip the overdued subscription and default to the 2nd one in the list
        self.assertEqual(storage_mock['subscriptions'][1]['name'], self.subscription1.display_name)
        self.assertTrue(storage_mock['subscriptions'][1]['isDefault'])

    def test_get_subscription(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)

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

    def test_get_auth_info_fail_on_user_account(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)

        consolidated = Profile._normalize_properties(self.user1,
                                                     [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)

        # testing dump of existing logged in account
        self.assertRaises(CLIError, profile.get_sp_auth_info)

    @mock.patch('azure.cli.core._profile.CLOUD', autospec=True)
    @mock.patch('azure.cli.core.profiles.get_api_version', autospec=True)
    def test_subscription_finder_constructor(self, get_api_mock, cloud_mock):
        get_api_mock.return_value = '2016-06-01'
        cloud_mock.endpoints.resource_manager = 'http://foo_arm'
        finder = SubscriptionFinder(None, None, arm_client_factory=None)
        result = finder._arm_client_factory(mock.MagicMock())
        self.assertEquals(result.config.base_url, 'http://foo_arm')

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_get_auth_info_for_logged_in_service_principal(self, mock_auth_context):
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = [self.subscription1]
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(storage_mock, use_global_creds_cache=False)
        profile._management_resource_uri = 'https://management.core.windows.net/'
        profile.find_subscriptions_on_login(False,
                                            '1234',
                                            'my-secret',
                                            True,
                                            self.tenant_id,
                                            False,
                                            finder)
        # action
        extended_info = profile.get_sp_auth_info()
        # assert
        self.assertEqual(self.id1.split('/')[-1], extended_info['subscriptionId'])
        self.assertEqual('1234', extended_info['clientId'])
        self.assertEqual('my-secret', extended_info['clientSecret'])
        self.assertEqual('https://login.microsoftonline.com', extended_info['activeDirectoryEndpointUrl'])
        self.assertEqual('https://management.azure.com/', extended_info['resourceManagerEndpointUrl'])

    def test_get_auth_info_for_newly_created_service_principal(self):
        storage_mock = {'subscriptions': []}
        profile = Profile(storage_mock, use_global_creds_cache=False)
        consolidated = Profile._normalize_properties(self.user1, [self.subscription1], False)
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
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = []
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(storage_mock, use_global_creds_cache=False)
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
        self.assertEqual(1, len(result))
        self.assertEqual(result[0]['id'], self.tenant_id)
        self.assertEqual(result[0]['state'], 'Enabled')
        self.assertEqual(result[0]['tenantId'], self.tenant_id)
        self.assertEqual(result[0]['name'], 'N/A(tenant level account)')

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_create_account_without_subscriptions_thru_common_tenant(self, mock_auth_context):
        mock_auth_context.acquire_token.return_value = self.token_entry1
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        tenant_object = mock.MagicMock()
        tenant_object.id = "foo-bar"
        tenant_object.tenant_id = self.tenant_id
        mock_arm_client = mock.MagicMock()
        mock_arm_client.subscriptions.list.return_value = []
        mock_arm_client.tenants.list.return_value = (x for x in [tenant_object])

        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)

        storage_mock = {'subscriptions': []}
        profile = Profile(storage_mock, use_global_creds_cache=False)
        profile._management_resource_uri = 'https://management.core.windows.net/'

        # action
        result = profile.find_subscriptions_on_login(False,
                                                     '1234',
                                                     'my-secret',
                                                     False,
                                                     None,
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
        finder = mock.MagicMock()
        finder.find_through_interactive_flow.return_value = []
        storage_mock = {'subscriptions': []}
        profile = Profile(storage_mock, use_global_creds_cache=False)

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
        profile = Profile(storage_mock, use_global_creds_cache=False)
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
        profile = Profile(use_global_creds_cache=False)
        cache = profile._creds_cache.adal_token_cache
        self.assertFalse(cache.read_items())
        self.assertTrue(mock_read_file.called)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_load_cached_tokens(self, mock_read_file):
        mock_read_file.return_value = [Test_Profile.token_entry1]
        profile = Profile(use_global_creds_cache=False)
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
        profile = Profile(storage_mock, use_global_creds_cache=False)
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
    @mock.patch('requests.post', autospec=True)
    def test_get_login_credentials_msi(self, mock_post, mock_read_cred_file):
        mock_read_cred_file.return_value = []

        # setup an existing msi subscription
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)
        test_subscription_id = '12345678-1bf0-4dda-aec3-cb9272f09590'
        test_tenant_id = '12345678-38d6-4fb2-bad9-b7b93a3e1234'
        test_port = '12345'
        test_user = 'VM'
        msi_subscription = SubscriptionStub('/subscriptions/' + test_subscription_id, 'MSI@' + str(test_port), self.state1, test_tenant_id)
        consolidated = Profile._normalize_properties(test_user,
                                                     [msi_subscription],
                                                     True)
        profile._set_subscriptions(consolidated)

        # setup a response for the token request
        test_token_entry = {
            'token_type': 'Bearer',
            'access_token': 'good token for you'
        }
        encoded_test_token = json.dumps(test_token_entry).encode()
        response = mock.MagicMock()
        response.status_code = 200
        response.content = encoded_test_token
        mock_post.return_value = response

        # action
        cred, subscription_id, _ = profile.get_login_credentials()

        # assert
        self.assertEqual(subscription_id, test_subscription_id)

        # verify the cred._tokenRetriever is a working lambda
        token_type, token, whole_entry = cred._token_retriever()
        self.assertEqual(test_token_entry['access_token'], token)
        self.assertEqual(test_token_entry['token_type'], token_type)
        self.assertEqual(test_token_entry, whole_entry)
        mock_post.assert_called_with('http://localhost:12345/oauth2/token',
                                     data={'resource': 'https://management.core.windows.net/'},
                                     headers={'Metadata': 'true'})

    @mock.patch('requests.post', autospec=True)
    @mock.patch('time.sleep', autospec=True)
    def test_msi_token_request_retries(self, mock_sleep, mock_post):
        # set up error case: #1 exception thrown, #2 error status
        bad_response = mock.MagicMock()
        bad_response.status_code = 400
        bad_response.text = 'just bad'

        test_token_entry = {
            'token_type': 'Bearer',
            'access_token': 'good token for you'
        }
        encoded_test_token = json.dumps(test_token_entry).encode()
        good_response = mock.MagicMock()
        good_response.status_code = 200
        good_response.content = encoded_test_token

        mock_post.side_effect = [ValueError('fail'), bad_response, good_response]

        # action
        token_type, token, whole_entry = Profile.get_msi_token('azure-resource', 12345)

        # assert
        self.assertEqual(test_token_entry['access_token'], token)
        self.assertEqual(test_token_entry['token_type'], token_type)
        self.assertEqual(test_token_entry, whole_entry)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_raw_token(self, mock_get_token, mock_read_cred_file):
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [Test_Profile.token_entry1]
        mock_get_token.return_value = (some_token_type, Test_Profile.raw_token1,
                                       Test_Profile.token_entry1)
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)
        consolidated = Profile._normalize_properties(self.user1,
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

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_login_credentials_for_graph_client(self, mock_get_token, mock_read_cred_file):
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [Test_Profile.token_entry1]
        mock_get_token.return_value = (some_token_type, Test_Profile.raw_token1)
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)
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

    def test_cloud_console_login(self):
        import tempfile
        from azure.cli.core.util import get_file_json
        from azure.cli.core._session import Session

        test_account = Session()
        test_dir = tempfile.mkdtemp()
        test_account_file = os.path.join(test_dir, 'azureProfile.json')
        test_account.load(test_account_file)
        # test_token_file = os.path.join(test_dir, 'accessTokens.json')

        os.environ['AZURE_CONFIG_DIR'] = test_dir

        # NOTE, do not use still valid tokens
        arm_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IjlGWERwYmZNRlQyU3ZRdVhoODQ2WVR3RUlCdyIsImtpZCI6IjlGWERwYmZNRlQyU3ZRdVhoODQ2WVR3RUlCdyJ9.eyJhdWQiOiJodHRwczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81NDgyNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEvIiwiaWF0IjoxNTAwMzEwMDA3LCJuYmYiOjE1MDAzMTAwMDcsImV4cCI6MTUwMDMxMzkwNywiYWNyIjoiMSIsImFpbyI6IlkyWmdZTGhrZTZyemJLTGtiNFpVbFZ1N1pyN1F1Uk8zOUsxSDZNbmUzcE85ekp1TU5SZ0EiLCJhbXIiOlsicHdkIl0sImFwcGlkIjoiMDRiMDc3OTUtOGRkYi00NjFhLWJiZWUtMDJmOWUxYmY3YjQ2IiwiYXBwaWRhY3IiOiIwIiwiZV9leHAiOjI2MjgwMCwiZmFtaWx5X25hbWUiOiJzZGsiLCJnaXZlbl9uYW1lIjoiYWRtaW4zIiwiZ3JvdXBzIjpbImU0YmIwYjU2LTEwMTQtNDBmOC04OGFiLTNkOGE4Y2IwZTA4NiIsIjhhOWIxNjE3LWZjOGQtNGFhOS1hNDJmLTk5ODY4ZDMxNDY5OSIsIjU0ODAzOTE3LTRjNzEtNGQ2Yy04YmRmLWJiZDkzMTAxMGY4YyJdLCJpcGFkZHIiOiIxNjcuMjIwLjAuMjM0IiwibmFtZSI6ImFkbWluMyIsIm9pZCI6ImU3ZTE1OGQzLTdjZGMtNDdjZC04ODI1LTU4NTlkN2FiMmI1NSIsInBsYXRmIjoiMTQiLCJwdWlkIjoiMTAwMzNGRkY5NUQ0NEU4NCIsInNjcCI6InVzZXJfaW1wZXJzb25hdGlvbiIsInN1YiI6ImhRenl3b3FTLUEtRzAySTl6ZE5TRmtGd3R2MGVwZ2lWY1Vsdm1PZEZHaFEiLCJ0aWQiOiI1NDgyNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEiLCJ1bmlxdWVfbmFtZSI6ImFkbWluM0BBenVyZVNES1RlYW0ub25taWNyb3NvZnQuY29tIiwidXBuIjoiYWRtaW4zQEF6dXJlU0RLVGVhbS5vbm1pY3Jvc29mdC5jb20iLCJ2ZXIiOiIxLjAiLCJ3aWRzIjpbIjYyZTkwMzk0LTY5ZjUtNDIzNy05MTkwLTAxMjE3NzE0NWUxMCJdfQ.I-hDlI5osimq7caHUkRAX55RWBDzt-EZl2vus2YUh-knZBlQEcJyfeUhtdZM2bTjaZNx5w3mJTuOfdNb3HSZ9VIgdvatN-Cp1FLFb2TAagTb_hJiVa613ZuQd-m_IZm3suAlTam-3GiqzlrkkPl1wQPv5Z8rSeHa8eEOUKvW0Y1aUuj17Cc3xVCkKu5K-q8eHZMbY-rCceWf25U4dqt7evW_95TokrPpw_KJvXWW-dg3TvTgHZgvyux9ydijCNcQlPE9kPdoHLgolbX4zCcto29-wsmyL5MlVH6etiHCQPRRgI0AUia3aPugTaOw5qKEWlc38DloGGKir64NiD82Jg'
        kv_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IjlGWERwYmZNRlQyU3ZRdVhoODQ2WVR3RUlCdyIsImtpZCI6IjlGWERwYmZNRlQyU3ZRdVhoODQ2WVR3RUlCdyJ9.eyJhdWQiOiJodHRwczovL3ZhdWx0LmF6dXJlLm5ldCIsImlzcyI6Imh0dHBzOi8vc3RzLndpbmRvd3MubmV0LzU0ODI2YjIyLTM4ZDYtNGZiMi1iYWQ5LWI3YjkzYTNlOWM1YS8iLCJpYXQiOjE1MDAzMTQ4MDUsIm5iZiI6MTUwMDMxNDgwNSwiZXhwIjoxNTAwMzE4NzA1LCJhY3IiOiIxIiwiYWlvIjoiWTJaZ1lCQ3dGSGhYY3FaczVsU2hvQWpWWXRsM0t5WEU1WHVXUmR1SzEreDZ4dDNidUFBQSIsImFtciI6WyJwd2QiXSwiYXBwaWQiOiIwNGIwNzc5NS04ZGRiLTQ2MWEtYmJlZS0wMmY5ZTFiZjdiNDYiLCJhcHBpZGFjciI6IjAiLCJlX2V4cCI6MjYyODAwLCJmYW1pbHlfbmFtZSI6InNkayIsImdpdmVuX25hbWUiOiJhZG1pbjMiLCJncm91cHMiOlsiZTRiYjBiNTYtMTAxNC00MGY4LTg4YWItM2Q4YThjYjBlMDg2IiwiOGE5YjE2MTctZmM4ZC00YWE5LWE0MmYtOTk4NjhkMzE0Njk5IiwiNTQ4MDM5MTctNGM3MS00ZDZjLThiZGYtYmJkOTMxMDEwZjhjIl0sImlwYWRkciI6IjE2Ny4yMjAuMS4yMzQiLCJuYW1lIjoiYWRtaW4zIiwib2lkIjoiZTdlMTU4ZDMtN2NkYy00N2NkLTg4MjUtNTg1OWQ3YWIyYjU1IiwicGxhdGYiOiIxNCIsInB1aWQiOiIxMDAzM0ZGRjk1RDQ0RTg0Iiwic2NwIjoidXNlcl9pbXBlcnNvbmF0aW9uIiwic3ViIjoidUVNS3FCYld2dFI0SERHZzg2TEdMMGY3dW5zQ0J6MGxlaTJjejE3QmZKRSIsInRpZCI6IjU0ODI2YjIyLTM4ZDYtNGZiMi1iYWQ5LWI3YjkzYTNlOWM1YSIsInVuaXF1ZV9uYW1lIjoiYWRtaW4zQEF6dXJlU0RLVGVhbS5vbm1pY3Jvc29mdC5jb20iLCJ1cG4iOiJhZG1pbjNAQXp1cmVTREtUZWFtLm9ubWljcm9zb2Z0LmNvbSIsInZlciI6IjEuMCJ9.A_3pa1F0qYNZdZE0AwN2YVuNf4aEhfKvkfQkgSHxty284W44VHORixceiDTEtgrM34a00KrRCo-oIMoho5_0mcQbelcjpwP8LSzLZOxk6zrTS0ZhBXywVf0fKD5lsUaOe3r2HnE5MLGzgtJotU72xKnVEslT0-q5miNcKQycx5rm3fUtq9RzETCk2s55qZtT4jdc5HL2HS9Kb8hYLS7VG7H59Rxhq5hoJue4Y7tArS25gIBVgTfUc2nsdj_316l12Cj3G6HXvUp9Gta7AMu6ivQoPSc2U8skOFhDlR7viAQeObWOG7GrERhNQnR2PDxTiJbB7sze_r6znJlVHPFBeQ'
        test_sub = Subscription()
        setattr(test_sub, 'id', 'id123')
        setattr(test_sub, 'subscription_id', 'id123')
        setattr(test_sub, 'display_name', 'good name')
        setattr(test_sub, 'state', SubscriptionState.enabled)
        setattr(test_sub, 'tenant_id', '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a')

        with mock.patch('azure.cli.core._profile.SubscriptionFinder._find_using_specific_tenant', autospec=True, return_value=[test_sub]):
            profile = Profile(use_global_creds_cache=False, storage=test_account)
            result_accounts = profile.find_subscriptions_in_cloud_console([arm_token, kv_token])

        # verify the local account
        expected_subscription = {
            "state": "Enabled",
            "user": {
                "type": "user",
                "name": "admin3@AzureSDKTeam.onmicrosoft.com"
            },
            "name": "good name",
            "isDefault": True,
            "id": "id123",
            "environmentName": "AzureCloud",
            "tenantId": "54826b22-38d6-4fb2-bad9-b7b93a3e9c5a"
        }
        self.assertEqual([expected_subscription], result_accounts)

        # verify the token file
        # expected_arm_token_entry = {
        #    "isMRRT": True,
        #    "_clientId": "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
        #    "accessToken": arm_token,
        #    "userId": "admin3@AzureSDKTeam.onmicrosoft.com",
        #    # "expiresOn": "2017-07-17 21:26:38.676587",
        #    "resource": "https://management.core.windows.net/",
        #    "expiresIn": "3600",
        #    "_authority": "https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a",
        #    "tokenType": "Bearer",
        #    "oid": "e7e158d3-7cdc-47cd-8825-5859d7ab2b55"
        # }
        # expected_keyvault_token_entry = {
        #    "isMRRT": True,
        #    "_clientId": "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
        #    "accessToken": kv_token,
        #    "userId": "admin3@AzureSDKTeam.onmicrosoft.com",
        #    # "expiresOn": "2017-07-17 21:26:38.676587",
        #    "resource": "https://vault.azure.net",
        #    "expiresIn": "3600",
        #    "_authority": "https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a",
        #    "tokenType": "Bearer",
        #    "oid": "e7e158d3-7cdc-47cd-8825-5859d7ab2b55"
        # }
        # actual = get_file_json(test_token_file)
        # # per design, 'expiresOn' will not be accurate but doesn't matter. Hence, skip the verification
        # for a in actual:
        #    a.pop('expiresOn')
        # TODO: Re-enable after issue #4053 is fixed
        # self.assertEqual([expected_arm_token_entry, expected_keyvault_token_entry], actual)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_login_credentials_for_data_lake_client(self, mock_get_token, mock_read_cred_file):
        some_token_type = 'Bearer'
        mock_read_cred_file.return_value = [Test_Profile.token_entry1]
        mock_get_token.return_value = (some_token_type, Test_Profile.raw_token1)
        # setup
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)
        consolidated = Profile._normalize_properties(self.user1, [self.subscription1],
                                                     False)
        profile._set_subscriptions(consolidated)
        # action
        cred, _, tenant_id = profile.get_login_credentials(
            resource=CLOUD.endpoints.active_directory_data_lake_resource_id)
        _, _ = cred._token_retriever()
        # verify
        mock_get_token.assert_called_once_with(mock.ANY, self.user1, self.tenant_id,
                                               'https://datalake.azure.net/')
        self.assertEqual(tenant_id, self.tenant_id)

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    @mock.patch('azure.cli.core._profile.CredsCache.persist_cached_creds', autospec=True)
    def test_logout(self, mock_persist_creds, mock_read_cred_file):
        # setup
        mock_read_cred_file.return_value = [Test_Profile.token_entry1]

        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)
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
        profile = Profile(storage_mock, use_global_creds_cache=False)
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

    @mock.patch('requests.post', autospec=True)
    @mock.patch('azure.cli.core.profiles._shared.get_client_class', autospec=True)
    def test_find_subscriptions_in_vm_with_msi(self, mock_get_client_class, mock_post):

        class ClientStub:
            def __init__(self, *args, **kwargs):
                self.subscriptions = mock.MagicMock()
                self.subscriptions.list.return_value = [Test_Profile.subscription1]

        mock_get_client_class.return_value = ClientStub

        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)

        test_token_entry = {
            'token_type': 'Bearer',
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IlZXVkljMVdEMVRrc2JiMzAxc2FzTTVrT3E1USIsImtpZCI6IlZXVkljMVdEMVRrc2JiMzAxc2FzTTVrT3E1USJ9.eyJhdWQiOiJodHRwczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81NDgyNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEvIiwiaWF0IjoxNTAzMzU0ODc2LCJuYmYiOjE1MDMzNTQ4NzYsImV4cCI6MTUwMzM1ODc3NiwiYWNyIjoiMSIsImFpbyI6IkFTUUEyLzhFQUFBQTFGL1k0VVR3bFI1Y091QXJxc1J0OU5UVVc2MGlsUHZna0daUC8xczVtdzg9IiwiYW1yIjpbInB3ZCJdLCJhcHBpZCI6IjA0YjA3Nzk1LThkZGItNDYxYS1iYmVlLTAyZjllMWJmN2I0NiIsImFwcGlkYWNyIjoiMCIsImVfZXhwIjoyNjI4MDAsImZhbWlseV9uYW1lIjoic2RrIiwiZ2l2ZW5fbmFtZSI6ImFkbWluMyIsImdyb3VwcyI6WyJlNGJiMGI1Ni0xMDE0LTQwZjgtODhhYi0zZDhhOGNiMGUwODYiLCI4YTliMTYxNy1mYzhkLTRhYTktYTQyZi05OTg2OGQzMTQ2OTkiLCI1NDgwMzkxNy00YzcxLTRkNmMtOGJkZi1iYmQ5MzEwMTBmOGMiXSwiaXBhZGRyIjoiMTY3LjIyMC4xLjIzNCIsIm5hbWUiOiJhZG1pbjMiLCJvaWQiOiJlN2UxNThkMy03Y2RjLTQ3Y2QtODgyNS01ODU5ZDdhYjJiNTUiLCJwdWlkIjoiMTAwMzNGRkY5NUQ0NEU4NCIsInNjcCI6InVzZXJfaW1wZXJzb25hdGlvbiIsInN1YiI6ImhRenl3b3FTLUEtRzAySTl6ZE5TRmtGd3R2MGVwZ2lWY1Vsdm1PZEZHaFEiLCJ0aWQiOiI1NDgyNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEiLCJ1bmlxdWVfbmFtZSI6ImFkbWluM0BBenVyZVNES1RlYW0ub25taWNyb3NvZnQuY29tIiwidXBuIjoiYWRtaW4zQEF6dXJlU0RLVGVhbS5vbm1pY3Jvc29mdC5jb20iLCJ1dGkiOiJuUEROYm04UFkwYUdELWhNeWxrVEFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyI2MmU5MDM5NC02OWY1LTQyMzctOTE5MC0wMTIxNzcxNDVlMTAiXX0.Pg4cq0MuP1uGhY_h51ZZdyUYjGDUFgTW2EfIV4DaWT9RU7GIK_Fq9VGBTTbFZA0pZrrmP-z7DlN9-U0A0nEYDoXzXvo-ACTkm9_TakfADd36YlYB5aLna-yO0B7rk5W9ANelkzUQgRfidSHtCmV6i4Ve-lOym1sH5iOcxfIjXF0Tp2y0f3zM7qCq8Cp1ZxEwz6xYIgByoxjErNXrOME5Ld1WizcsaWxTXpwxJn_Q8U2g9kXHrbYFeY2gJxF_hnfLvNKxUKUBnftmyYxZwKi0GDS0BvdJnJnsqSRSpxUx__Ra9QJkG1IaDzjZcSZPHK45T6ohK9Hk9ktZo0crVl7Tmw'
        }
        encoded_test_token = json.dumps(test_token_entry).encode()
        good_response = mock.MagicMock()
        good_response.status_code = 200
        good_response.content = encoded_test_token
        mock_post.return_value = good_response

        subscriptions = profile.find_subscriptions_in_vm_with_msi('9999')

        # assert
        self.assertEqual(len(subscriptions), 1)
        s = subscriptions[0]
        self.assertEqual(s['user']['name'], 'VM')
        self.assertEqual(s['user']['type'], 'servicePrincipal')
        self.assertEqual(s['name'], 'MSI@9999')
        self.assertEqual(s['id'], self.id1.split('/')[-1])
        self.assertEqual(s['tenantId'], '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a')

    @mock.patch('adal.AuthenticationContext.acquire_token_with_username_password', autospec=True)
    @mock.patch('adal.AuthenticationContext.acquire_token', autospec=True)
    @mock.patch('azure.cli.core._profile.CLOUD', autospec=True)
    def test_find_subscriptions_thru_username_password_adfs(self, mock_get_cloud, mock_acquire_token,
                                                            mock_acquire_token_username_password):
        TEST_ADFS_AUTH_URL = 'https://adfs.local.azurestack.external/adfs'

        def test_acquire_token(self, resource, username, password, client_id):
            global acquire_token_invoked
            acquire_token_invoked = True
            if (self.authority.url == TEST_ADFS_AUTH_URL and self.authority.is_adfs_authority):
                return Test_Profile.token_entry1
            else:
                raise ValueError('AuthContext was not initialized correctly for ADFS')

        mock_acquire_token_username_password.side_effect = test_acquire_token
        mock_acquire_token.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = [self.subscription1]
        mock_get_cloud.endpoints.active_directory = TEST_ADFS_AUTH_URL
        finder = SubscriptionFinder(_AUTH_CTX_FACTORY,
                                    None,
                                    lambda _: mock_arm_client)
        mgmt_resource = 'https://management.core.windows.net/'
        # action
        subs = finder.find_from_user_account(self.user1, 'bar', None, mgmt_resource)

        # assert
        self.assertEqual([self.subscription1], subs)
        self.assertTrue(acquire_token_invoked)

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

    @mock.patch('adal.AuthenticationContext', autospec=True)
    def test_refresh_accounts_one_user_account(self, mock_auth_context):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)
        consolidated = Profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False)
        profile._set_subscriptions(consolidated)
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        mock_auth_context.acquire_token.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = deepcopy([self.subscription1, self.subscription2])
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)
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
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)
        sp_subscription1 = SubscriptionStub('sp-sub/3', 'foo-subname', self.state1, 'foo_tenant.onmicrosoft.com')
        consolidated = Profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False)
        consolidated += Profile._normalize_properties('http://foo', [sp_subscription1], True)
        profile._set_subscriptions(consolidated)
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        mock_auth_context.acquire_token.return_value = self.token_entry1
        mock_auth_context.acquire_token_with_client_credentials.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.side_effect = deepcopy([[self.subscription1], [self.subscription2, sp_subscription1]])
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)
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
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)
        consolidated = Profile._normalize_properties(self.user1, deepcopy([self.subscription1]), False)
        profile._set_subscriptions(consolidated)
        mock_auth_context.acquire_token_with_username_password.return_value = self.token_entry1
        mock_auth_context.acquire_token.return_value = self.token_entry1
        mock_arm_client = mock.MagicMock()
        mock_arm_client.tenants.list.return_value = [TenantStub(self.tenant_id)]
        mock_arm_client.subscriptions.list.return_value = []
        finder = SubscriptionFinder(lambda _, _2: mock_auth_context,
                                    None,
                                    lambda _: mock_arm_client)
        # action
        profile.refresh_accounts(finder)

        # assert
        result = storage_mock['subscriptions']
        self.assertEqual(0, len(result))

    @mock.patch('azure.cli.core._profile._load_tokens_from_file', autospec=True)
    def test_credscache_load_tokens_and_sp_creds_with_secret(self, mock_read_file):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_read_file.return_value = [self.token_entry1, test_sp]

        # action
        creds_cache = CredsCache(async_persist=False)

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
        creds_cache = CredsCache(async_persist=False)
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
        creds_cache = CredsCache(async_persist=False)

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
        creds_cache = CredsCache(async_persist=False)

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
        creds_cache = CredsCache(async_persist=False)

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
        creds_cache = CredsCache(auth_ctx_factory=get_auth_context, async_persist=False)

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

    @mock.patch('azure.cli.core._profile.CLOUD', autospec=True)
    def test_detect_adfs_authority_url(self, mock_get_cloud):
        adfs_url_1 = 'https://adfs.redmond.ext-u15f2402.masd.stbtest.microsoft.com/adfs/'
        mock_get_cloud.endpoints.active_directory = adfs_url_1
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock, use_global_creds_cache=False)

        # test w/ trailing slash
        r = profile.auth_ctx_factory('common', None)
        self.assertEqual(r.authority.url, adfs_url_1)

        # test w/o trailing slash
        adfs_url_2 = 'https://adfs.redmond.ext-u15f2402.masd.stbtest.microsoft.com/adfs'
        mock_get_cloud.endpoints.active_directory = adfs_url_2
        r = profile.auth_ctx_factory('common', None)
        self.assertEqual(r.authority.url, adfs_url_2)

        # test w/ regular aad
        aad_url = 'https://login.microsoftonline.com'
        mock_get_cloud.endpoints.active_directory = aad_url
        r = profile.auth_ctx_factory('common', None)
        self.assertEqual(r.authority.url, aad_url + '/common')


class FileHandleStub(object):  # pylint: disable=too-few-public-methods

    def write(self, content):
        pass

    def __enter__(self):
        return self

    def __exit__(self, _2, _3, _4):
        pass


class SubscriptionStub(Subscription):  # pylint: disable=too-few-public-methods

    def __init__(self, id, display_name, state, tenant_id):  # pylint: disable=redefined-builtin
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
