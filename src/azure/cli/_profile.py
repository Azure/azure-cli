import collections
from msrest.authentication import BasicTokenAuthentication
from .main import CONFIG

class Profile(object):

    def __init__(self, storage=CONFIG):
        self._storage = storage

    @staticmethod
    def normalize_properties(user, subscriptions):
        consolidated = []
        for s in subscriptions:
            consolidated.append({
                'id': s.id.rpartition('/')[2],
                'name': s.display_name,
                'state': s.state,
                'user': user,
                'active': False
                })
        return consolidated

    def set_subscriptions(self, new_subscriptions, access_token):
        existing_ones = self.load_subscriptions()
        active_one = next((x for x in existing_ones if x['active']), None)
        active_subscription_id = active_one['id'] if active_one else None

        #merge with existing ones
        dic = collections.OrderedDict((x['id'], x) for x in existing_ones)
        dic.update((x['id'], x) for x in new_subscriptions)
        subscriptions = list(dic.values())

        if active_one:
            new_active_one = next(
                (x for x in new_subscriptions if x['id'] == active_subscription_id), None)

            for s in subscriptions:
                s['active'] = False

            if not new_active_one:
                new_active_one = new_subscriptions[0]
            new_active_one['active'] = True
        else:
            new_subscriptions[0]['active'] = True

        #before adal/python is available, persist tokens with other profile info
        for s in new_subscriptions:
            s['access_token'] = access_token

        self._save_subscriptions(subscriptions)

    def get_login_credentials(self):
        subscriptions = self.load_subscriptions()
        if not subscriptions:
            raise ValueError('Please run login to setup account.')

        active = [x for x in subscriptions if x['active']]
        if len(active) != 1:
            raise ValueError('Please run "account set" to select active account.')

        return BasicTokenAuthentication(
            {'access_token': active[0]['access_token']}), active[0]['id']

    def set_active_subscription(self, subscription_id_or_name):
        subscriptions = self.load_subscriptions()

        subscription_id_or_name = subscription_id_or_name.lower()
        result = [x for x in subscriptions
                  if subscription_id_or_name == x['id'].lower() or
                  subscription_id_or_name == x['name'].lower()]

        if len(result) != 1:
            raise ValueError('The subscription of "{}" does not exist or has more than'
                             ' one match.'.format(subscription_id_or_name))

        for s in subscriptions:
            s['active'] = False
        result[0]['active'] = True

        self._save_subscriptions(subscriptions)

    def logout(self, user):
        subscriptions = self.load_subscriptions()
        result = [x for x in subscriptions if user.lower() == x['user'].lower()]
        subscriptions = [x for x in subscriptions if x not in result]

        #reset the active subscription if needed
        result = [x for x in subscriptions if x['active']]
        if not result and subscriptions:
            subscriptions[0]['active'] = True

        self._save_subscriptions(subscriptions)

    def load_subscriptions(self):
        return self._storage.get('subscriptions') or []

    def _save_subscriptions(self, subscriptions):
        self._storage['subscriptions'] = subscriptions
