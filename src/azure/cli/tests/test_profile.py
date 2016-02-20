import unittest
from azure.cli._profile import Profile

class Test_Profile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.user1 = 'foo@foo.com'
        cls.id1 = 'subscriptions/1'
        cls.display_name1 = 'foo account'
        cls.state1 = 'enabled'
        cls.subscription1 = SubscriptionStub(cls.id1, 
                                             cls.display_name1, 
                                             cls.state1)
        cls.token1 = 'token1'

        cls.user2 = 'bar@bar.com'
        cls.id2 = 'subscriptions/2'
        cls.display_name2 = 'bar account'
        cls.state2 = 'suspended'
        cls.subscription2 = SubscriptionStub(cls.id2, 
                                             cls.display_name2, 
                                             cls.state2)
        cls.token2 = 'token2'

    def test_normalize(self):
        consolidated = Profile.normalize_properties(self.user1, 
                                                    [self.subscription1])
        self.assertEqual(consolidated[0], {
            'id': '1',
            'name': self.display_name1,
            'state': self.state1,
            'user': self.user1,
            'active': False
            })

    def test_update_add_two_different_subscriptions(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        #add the first and verify
        consolidated = Profile.normalize_properties(self.user1, 
                                                    [self.subscription1])
        profile.set_subscriptions(consolidated, self.token1)

        self.assertEqual(len(storage_mock['subscriptions']), 1)
        subscription1 = storage_mock['subscriptions'][0]
        self.assertEqual(subscription1, { 
            'id': '1',
            'name': self.display_name1,
            'state': self.state1,
            'user': self.user1,
            'access_token': self.token1,
            'active': True
            })

        #add the second and verify
        consolidated = Profile.normalize_properties(self.user2, 
                                                    [self.subscription2])
        profile.set_subscriptions(consolidated, self.token2)

        self.assertEqual(len(storage_mock['subscriptions']), 2)
        subscription2 = storage_mock['subscriptions'][1]
        self.assertEqual(subscription2, { 
            'id': '2',
            'name': self.display_name2,
            'state': self.state2,
            'user': self.user2,
            'access_token': self.token2,
            'active': True
            })

        #verify the old one stays, but no longer active
        self.assertEqual(storage_mock['subscriptions'][0]['name'],
                         subscription1['name']) 
        self.assertEqual(storage_mock['subscriptions'][0]['access_token'], 
                          self.token1)
        self.assertFalse(storage_mock['subscriptions'][0]['active']) 

    def test_update_with_same_subscription_added_twice(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        #add one twice and verify we will have one but with new token
        consolidated = Profile.normalize_properties(self.user1, 
                                                    [self.subscription1])
        profile.set_subscriptions(consolidated, self.token1)

        new_subscription1 = SubscriptionStub(self.id1, 
                                            self.display_name1, 
                                            self.state1)
        consolidated = Profile.normalize_properties(self.user1, 
                                                    [new_subscription1])
        profile.set_subscriptions(consolidated, self.token2)

        self.assertEqual(len(storage_mock['subscriptions']), 1)
        self.assertEqual(storage_mock['subscriptions'][0]['access_token'], 
                          self.token2)
        self.assertTrue(storage_mock['subscriptions'][0]['active'])

    def test_set_active_subscription(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        consolidated = Profile.normalize_properties(self.user1, 
                                                    [self.subscription1])
        profile.set_subscriptions(consolidated, self.token1)

        consolidated = Profile.normalize_properties(self.user2, 
                                                    [self.subscription2])
        profile.set_subscriptions(consolidated, self.token2)

        subscription1 = storage_mock['subscriptions'][0]
        subscription2 = storage_mock['subscriptions'][1]
        self.assertTrue(subscription2['active'])

        profile.set_active_subscription(subscription1['id'])
        self.assertFalse(subscription2['active'])
        self.assertTrue(subscription1['active'])

    def test_get_login_credentials(self):
        storage_mock = {'subscriptions': None}
        profile = Profile(storage_mock)

        consolidated = Profile.normalize_properties(self.user1, 
                                                    [self.subscription1])
        profile.set_subscriptions(consolidated, self.token1)
        cred, subscription_id = profile.get_login_credentials()

        self.assertEqual(cred.token['access_token'], self.token1)
        self.assertEqual(subscription_id, '1')


class SubscriptionStub:
   def __init__(self, id, display_name, state):
       self.id = id
       self.display_name = display_name
       self.state = state

if __name__ == '__main__':
    unittest.main()
