from azure.cli.commands import CliArgumentType, register_cli_argument
from .custom import load_subscriptions
# BASIC PARAMETER CONFIGURATION

def get_subscription_id_list(prefix, **kwargs):#pylint: disable=unused-argument
    subscriptions = load_subscriptions()
    result = []
    for subscription in subscriptions:
        result.append(subscription['id'])
        result.append(subscription['name'])
    return result

password_type = CliArgumentType(
    options_list=('--password', '-p'),
    help='User password or client secret. Will prompt if not given.'
)

service_principal_type = CliArgumentType(
    action='store_true',
    help='The credential representing a service principal.'
)

subscription_name_or_id_type = CliArgumentType(
    options_list=('--subscription-name-or-id', '-n'),
    metavar='SUBSCRIPTION_NAME_OR_ID',
    help='Subscription id. Unique name also works.',
    completer=get_subscription_id_list
)

tenant_type = CliArgumentType(
    options_list=('--tenant', '-t'),
    help='The tenant associated with the service principal.'
)

username_type = CliArgumentType(
    options_list=('--username', '-u'),
    help='Organization id or service principal'
)

sp_name_type = CliArgumentType(
    options_list=('--name', '-n')
)

register_cli_argument('login', 'password', password_type)
register_cli_argument('login', 'service_principal', service_principal_type)
register_cli_argument('login', 'username', username_type)
register_cli_argument('login', 'tenant', tenant_type)

register_cli_argument('logout', 'username', username_type,
                      help='account user, if missing, logout the current active account')

register_cli_argument('account', 'subscription_name_or_id', subscription_name_or_id_type)

register_cli_argument('account create-sp', 'name', sp_name_type)
register_cli_argument('account reset-sp-credentials', 'name', sp_name_type)
