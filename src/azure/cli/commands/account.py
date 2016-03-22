from .._profile import Profile
from ..commands import CommandTable
from .._locale import L

command_table = CommandTable()

def get_command_table():
    return command_table

@command_table.command('account list')
#@description(L('List the imported subscriptions.'))
def list_subscriptions(args, unexpected): #pylint: disable=unused-argument
    profile = Profile()
    subscriptions = profile.load_subscriptions()

    return subscriptions

#@description(L('Set the current subscription'))
@command_table.option('--subscription-id -n', metavar='SUBSCRIPTION_ID', dest='subscription_id', help=L('Subscription Id, unique name also works.'))
@command_table.command('account set')
def set_active_subscription(args, unexpected): #pylint: disable=unused-argument
    subscription_id = args.get('subscription-id')
    if not id:
        raise ValueError(L('Please provide subscription id or unique name.'))

    profile = Profile()
    profile.set_active_subscription(subscription_id)
