from azure.cli.commands.argument_types import CliArgumentType, register_cli_argument

# BASIC PARAMETER CONFIGURATION

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
    help='Subscription id. Unique name also works.'
)

tenant_type = CliArgumentType(
    options_list=('--tenant', '-t'),
    help='The tenant associated with the service principal.'
)

username_type = CliArgumentType(
    options_list=('--username', '-u'),
    help='Organization id or service principal'
)

register_cli_argument('login', 'password', password_type)
register_cli_argument('login', 'service_principal', service_principal_type)
register_cli_argument('login', 'username', username_type)
register_cli_argument('login', 'tenant', tenant_type)

register_cli_argument('logout', 'username', username_type)

register_cli_argument('account', 'subscription_name_or_id', subscription_name_or_id_type)
