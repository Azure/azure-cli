from .._profile import Profile
from ..commands import command, description, option

@command('account list')
@description(_('List the imported subscriptions.'))
def list_subscriptions(args, unexpected):
    profile = Profile()
    subscriptions = profile.load_subscriptions()

    return subscriptions

@command('account set')
@description(_('Set the current subscription'))
@option('--subscription-id -n <subscription-id>', _('Subscription Id, unique name also works.'))
def set_active_subscription(args, unexpected):
    id = args.get('subscription-id')
    if not id:
        raise ValueError(_('Please provide subscription id or unique name.'))

    profile = Profile()
    profile.set_active_subscription(id)
