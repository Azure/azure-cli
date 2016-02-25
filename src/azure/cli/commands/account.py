from .._profile import Profile
from .._util import TableOutput
from ..commands import command, description, option

@command('account list')
@description(_('List the imported subscriptions.'))
def list_subscriptions(args, unexpected):
    profile = Profile()
    subscriptions = profile.load_subscriptions()

    with TableOutput() as to:
        for subscription in subscriptions:
            to.cell('Name', subscription['name'])
            to.cell('Active', bool(subscription['active']))
            to.cell('User', subscription['user'])
            to.cell('Subscription Id', subscription['id'])
            to.cell('State', subscription['state'])
            to.end_row()

@command('account set')
@description(_('Set the current subscription'))
@option('--subscription-id -n <subscription-id>', _('Subscription Id, unique name also works.'))
def set_active_subscription(args, unexpected):
    id = args.get('subscription-id')
    if not id:
        raise ValueError(_('Please provide subscription id or unique name.'))

    profile = Profile()
    profile.set_active_subscription(id)
