from azure.cli._profile import Profile
from azure.cli.commands import CommandTable
from azure.cli._locale import L
from .command_tables import COMMAND_TABLES
import azure.cli._logging as _logging

logger = _logging.getAzLogger(__name__)

command_table = CommandTable()

COMMAND_TABLES.append(command_table)

@command_table.command('account list', description=L('List the imported subscriptions.'))
def list_subscriptions(_):
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
    subscription_name_or_id = args.get('subscription-name-or-id')
    if not id:
        raise ValueError(L('Please provide subscription id or unique name.'))

    profile = Profile()
    profile.set_active_subscription(subscription_name_or_id)
