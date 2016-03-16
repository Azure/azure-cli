from .._profile import Profile
from ..commands import command, description, option
from .._locale import L

@command('account list')
@description(L('List the imported subscriptions.'))
def list_subscriptions(args, unexpected): #pylint: disable=unused-argument
    profile = Profile()
    subscriptions = profile.load_subscriptions()

    return subscriptions

@command('account set')
@description(L('Set the current subscription'))
@option('--subscription-id -n <subscription-id>',
        L('Subscription Id, unique name also works.'),
        required=True)
def set_active_subscription(args, unexpected): #pylint: disable=unused-argument
    subscription_id = args.get('subscription-id')
    if not id:
        raise ValueError(L('Please provide subscription id or unique name.'))

    profile = Profile()
    profile.set_active_subscription(subscription_id)
