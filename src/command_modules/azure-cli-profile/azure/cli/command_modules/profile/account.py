from azure.cli._profile import Profile
from azure.cli.commands import CommandTable
from azure.cli._locale import L
from .command_tables import COMMAND_TABLES
from azure.cli._logging import logger

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
    if not subscriptions:
        logger.warning('Please run "az login" to access your accounts.')
    return subscriptions

@command_table.command('account set')
@command_table.description(L('Set the current subscription'))
@command_table.option('--subscription-name-or-id -n',
                      metavar='SUBSCRIPTION_NAME_OR_ID',
                      dest='subscription_name_or_id',
                      help=L('Subscription Id, unique name also works.'),
                      required=True)
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
    subscription_name_or_id = args.get('subscription-name-or-id')
    if not id:
        raise ValueError(L('Please provide subscription id or unique name.'))

    profile = Profile()
    profile.set_active_subscription(subscription_name_or_id)
