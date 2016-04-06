from azure.cli._profile import Profile
from azure.cli.commands import CommandTable
from azure.cli._locale import L
from .command_tables import COMMAND_TABLES

command_table = CommandTable()

COMMAND_TABLES.append(command_table)

@command_table.command('account list', description=L('List the imported subscriptions.'))
def list_subscriptions(_):
    """
    type: command
    long-summary: |
        this module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2
    parameters:
    examples:
        - name: foo example
          text: example details
    """
    profile = Profile()
    subscriptions = profile.load_cached_subscriptions()

    return subscriptions

@command_table.command('account set')
@command_table.description(L('Set the current subscription'))
@command_table.option('--subscription-id -n', metavar='SUBSCRIPTION_ID', dest='subscription_id',
                      help=L('Subscription Id, unique name also works.'))
def set_active_subscription(args):
    """
    type: command
    short-summary: this module does xyz one-line or so
    long-summary: |
        this module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2
    parameters:
    examples:
        - name: foo example
          text: example details
    """
    subscription_id = args.get('subscription-id')
    if not id:
        raise ValueError(L('Please provide subscription id or unique name.'))

    profile = Profile()
    profile.set_active_subscription(subscription_id)
