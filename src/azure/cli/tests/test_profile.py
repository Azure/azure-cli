import json
import unittest
import mock
import adal
from azure.cli._profile import Profile, CredsCache, SubscriptionFinder, _AUTH_CTX_FACTORY
from azure.cli._azure_env import ENV_DEFAULT

class Test_Profile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tenant_id = 'microsoft.com'
        cls.user1 = 'foo@foo.com'
        cls.id1 = 'subscriptions/1'
        cls.display_name1 = 'foo account'
        cls.state1 = 'enabled'
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
        cls.state2 = 'suspended'
        cls.subscription2 = SubscriptionStub(cls.id2, 
                                             cls.display_name2, 
                                             cls.state2,
                                             cls.tenant_id)

    def test_normalize(self):
        consolidated = Profile._normalize_properties(self.user1, 
                                                    [self.subscription1],
                                                    False,
                                                    ENV_DEFAULT)
        expected = {
            'environmentName': 'AzureCloud',
            'id': '1',
            'name': self.display_name1,
            'state': self.state1,
            'user': {
                'name':self.user1,
                'type':'user'
                },
            'isDefault': False,
            'tenantId': self.tenant_id
            }
        self.assertEqual(expected, consolidated[0])

    def test_update_add_two_different_subscriptions(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        #add the first and verify
        consolidated = Profile._normalize_properties(self.user1, 
                                                    [self.subscription1],
                                                    False,
                                                    ENV_DEFAULT)
        profile._set_subscriptions(consolidated)

        self.assertEqual(len(storage_mock['subscriptions']), 1)
        subscription1 = storage_mock['subscriptions'][0]
        self.assertEqual(subscription1, {
            'environmentName': 'AzureCloud',
            'id': '1',
            'name': self.display_name1,
            'state': self.state1,
            'user': {
                'name': self.user1,
                'type': 'user'
                },
            'isDefault': True,
            'tenantId': self.tenant_id
            })

        #add the second and verify
        consolidated = Profile._normalize_properties(self.user2, 
                                                    [self.subscription2],
                                                    False,
                                                    ENV_DEFAULT)
        profile._set_subscriptions(consolidated)

        self.assertEqual(len(storage_mock['subscriptions']), 2)
        subscription2 = storage_mock['subscriptions'][1]
        self.assertEqual(subscription2, {
            'environmentName': 'AzureCloud',
            'id': '2',
            'name': self.display_name2,
            'state': self.state2,
            'user': {
                'name': self.user2,
                'type': 'user'
                },
            'isDefault': True,
            'tenantId': self.tenant_id
            })

        #verify the old one stays, but no longer active
        self.assertEqual(storage_mock['subscriptions'][0]['name'],
                         subscription1['name']) 
        self.assertFalse(storage_mock['subscriptions'][0]['isDefault']) 

    def test_update_with_same_subscription_added_twice(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        #add one twice and verify we will have one but with new token
        consolidated = Profile._normalize_properties(self.user1, 
                                                    [self.subscription1],
                                                    False,
                                                    ENV_DEFAULT)
        profile._set_subscriptions(consolidated)

        new_subscription1 = SubscriptionStub(self.id1, 
                                            self.display_name1, 
                                            self.state1,
                                            self.tenant_id)
        consolidated = Profile._normalize_properties(self.user1, 
                                                    [new_subscription1],
                                                    False,
                                                    ENV_DEFAULT)
        profile._set_subscriptions(consolidated)

        self.assertEqual(len(storage_mock['subscriptions']), 1)
        self.assertTrue(storage_mock['subscriptions'][0]['isDefault'])

    def test_set_active_subscription(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        consolidated = Profile._normalize_properties(self.user1, 
                                                    [self.subscription1],
                                                    False,
                                                    ENV_DEFAULT)
        profile._set_subscriptions(consolidated)

        consolidated = profile._normalize_properties(self.user2, 
                                                    [self.subscription2],
                                                    False,
                                                    ENV_DEFAULT)
        profile._set_subscriptions(consolidated)

        subscription1 = storage_mock['subscriptions'][0]
        subscription2 = storage_mock['subscriptions'][1]
        self.assertTrue(subscription2['isDefault'])

        profile.set_active_subscription(subscription1['id'])
        self.assertFalse(subscription2['isDefault'])
        self.assertTrue(subscription1['isDefault'])

    @mock.patch('azure.cli._profile._read_file_content', return_value=None)
    def test_create_token_cache(self, mock_read_file):
        profile = Profile()
        cache = profile._creds_cache.adal_token_cache
        self.assertFalse(cache.read_items())
        self.assertTrue(mock_read_file.called)

    @mock.patch('azure.cli._profile._read_file_content', autospec=True)
    def test_load_cached_tokens(self, mock_read_file):
        mock_read_file.return_value = json.dumps([Test_Profile.token_entry1])
        profile = Profile()
        cache = profile._creds_cache.adal_token_cache
        matched = cache.find({
            "_authority": "https://login.microsoftonline.com/common",
            "_clientId": "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
             "userId": self.user1
            })
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]['accessToken'], self.raw_token1)
    
    @mock.patch('azure.cli._profile._read_file_content', autospec=True)
    @mock.patch('azure.cli._profile.CredsCache.retrieve_token_for_user', autospec=True)
    def test_get_login_credentials(self, mock_get_token, mock_read_cred_file):
        mock_read_cred_file.return_value = json.dumps([Test_Profile.token_entry1])
        mock_get_token.return_value = Test_Profile.raw_token1
        #setup
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)
        consolidated = Profile._normalize_properties(self.user1, 
                                                [self.subscription1],
                                                False,
                                                ENV_DEFAULT)
        profile._set_subscriptions(consolidated)
        #action
        cred, subscription_id = profile.get_login_credentials()

        #verify
        self.assertEqual(subscription_id, '1')
        self.assertEqual(cred.token['access_token'], self.raw_token1)
        self.assertEqual(mock_read_cred_file.call_count, 1)
        self.assertEqual(mock_get_token.call_count, 1)
 
    @mock.patch('azure.cli._profile._read_file_content', autospec=True)
    @mock.patch('azure.cli._profile.CredsCache.persist_cached_creds', autospec=True)
    def test_logout(self, mock_persist_creds, mock_read_cred_file):
        #setup
        mock_read_cred_file.return_value = json.dumps([Test_Profile.token_entry1])

        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)
        consolidated = Profile._normalize_properties(self.user1, 
                                                [self.subscription1],
                                                False,
                                                ENV_DEFAULT)
        profile._set_subscriptions(consolidated)
        self.assertEqual(1, len(storage_mock['subscriptions']))
        #action
        profile.logout(self.user1)

        #verify
        self.assertEqual(0, len(storage_mock['subscriptions']))
        self.assertEqual(mock_read_cred_file.call_count, 1)
        self.assertEqual(mock_persist_creds.call_count, 1)

    def test_find_subscriptions_thru_username_password(self):
        finder = SubscriptionFinder(lambda _,_2:AuthenticationContextStub(Test_Profile), 
                                    None,
                                    lambda _: ArmClientStub(Test_Profile))
        subs = finder.find_from_user_account('foo', 'bar')
        self.assertEqual([self.subscription1], subs)

    def test_find_through_interactive_flow(self):
        finder = SubscriptionFinder(lambda _,_2:AuthenticationContextStub(Test_Profile), 
                                    None,
                                    lambda _: ArmClientStub(Test_Profile))
        subs = finder.find_through_interactive_flow()
        self.assertEqual([self.subscription1], subs)

    def test_find_from_service_principal_id(self):
        finder = SubscriptionFinder(lambda _,_2:AuthenticationContextStub(Test_Profile), 
                                    None,
                                    lambda _: ArmClientStub(Test_Profile))
        subs = finder.find_from_service_principal_id('my app', 'my secret', self.tenant_id)
        self.assertEqual([self.subscription1], subs)

class SubscriptionStub:
    def __init__(self, id, display_name, state, tenant_id):
       self.id = id
       self.display_name = display_name
       self.state = state
       self.tenant_id = tenant_id

class AuthenticationContextStub:
    def __init__(self, test_profile_cls, return_token1=True):
        #we need to reference some pre-defined test artifacts in Test_Profile
        self._test_profile_cls = test_profile_cls
        if not return_token1:
            raise ValueError('Please update to return other test tokens')

    def acquire_token_with_username_password(self, _, _2, _3, _4):
        return self._test_profile_cls.token_entry1

    def acquire_token_with_device_code(self, _, _2, _3):
        return self._test_profile_cls.token_entry1

    def acquire_token_with_client_credentials(self, _, _2, _3):
        return self._test_profile_cls.token_entry1

    def acquire_token(self, _, _2, _3):
        return self._test_profile_cls.token_entry1

    def acquire_user_code(self, _, _2):
        return {'message': 'secret code for you'}

class ArmClientStub:
    class TenantStub:
        def __init__(self, tenant_id):
            self.tenant_id = tenant_id

    class OperationsStub:
        def __init__(self, list_result):
            self._list_result = list_result

        def list(self):
            return self._list_result

    def __init__(self, test_profile_cls, use_tenant1_and_subscription1=True):
        self._test_profile_cls = test_profile_cls
        if use_tenant1_and_subscription1:
            self.tenants = ArmClientStub.OperationsStub([ArmClientStub.TenantStub(test_profile_cls.tenant_id)])    
            self.subscriptions = ArmClientStub.OperationsStub([test_profile_cls.subscription1])
        else:
            raise ValueError('Please update to return other test subscriptions')

if __name__ == '__main__':
    unittest.main()
