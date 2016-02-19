from msrest.authentication import BasicTokenAuthentication

from .main import CONFIG

class Profile(object):

    def update(self, subscriptions, access_token):
        subscriptions[0]['active'] = True
        CONFIG['subscriptions'] = subscriptions
        CONFIG['access_token'] = access_token

    def get_credentials(self):
        subscriptions = CONFIG['subscriptions']
        sub = [x for x in subscriptions if x['active'] == True ]
        if not sub and subscriptions:
            sub = subscriptions

        if sub:
            return (BasicTokenAuthentication({ 'access_token': CONFIG['access_token']}), 
                sub[0]['id'] )
        else:
            raise ValueError('you need to login to')