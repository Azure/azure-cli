from msrest.authentication import BasicTokenAuthentication

from .main import CONFIG

def get_access_token():
    return CONFIG['access_token']

def set_access_token(str):
    CONFIG['access_token'] = str

def get_subscriptions():
    return CONFIG['subscriptions']

def set_subscriptions(subscriptions, active_subscription):
    active_subscription['active'] = True
    CONFIG['subscriptions'] = subscriptions

def get_active_subscription():
    active_subscriptions = [x for x in get_subscriptions() if x['active']]

    if len(active_subscriptions) != 1:
        raise ProfileException("There can only be one active subscription, found {0}".format(len(active_subscriptions)))

    return active_subscriptions[0]

def set_active_subscription(id):
    subscriptions = [x for x in get_subscriptions() if x['id'] == id]

    if len(subscriptions) != 1:
        raise ProfileException("Expected 1 subscription, but found {0}".format(len(subscriptions)))

    active_subscription = get_active_subscription()
    active_subscription['active'] = False
    subscriptions[0]['active'] = True
    CONFIG.save()

def get_login_credentials():
    subscription = get_active_subscription()

    if not subscription:
        raise ValueError('Login has expired, please login again')

    return (BasicTokenAuthentication({ 'access_token': get_access_token() }), subscription['id'] )


class ProfileException(Exception):
    pass

