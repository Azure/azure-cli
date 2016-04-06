from azure.cli._profile import Profile
from azure.cli.commands import CommandTable
from azure.cli._locale import L
#TODO: update adal-python to support it
#from azure.cli._debug import should_disable_connection_verify

from .command_tables import COMMAND_TABLES

command_table = CommandTable()

COMMAND_TABLES.append(command_table)

@command_table.command('login')
@command_table.description(L('log in to an Azure subscription using Active Directory Organization Id')) # pylint: disable=line-too-long
@command_table.option('--username -u',
                      help=L('organization Id or service principal. Microsoft Account is not yet supported.')) # pylint: disable=line-too-long
@command_table.option('--password -p',
                      help=L('user password or client secret, will prompt if not given.'))
@command_table.option('--service-principal',
                      action='store_true',
                      help=L('the credential represents a service principal.'))
@command_table.option('--tenant -t', help=L('the tenant associated with the service principal.'))
def login(args):
    interactive = False

    username = args.get('username')
    password = None
    if username:
        password = args.get('password')
        if not password:
            import getpass
            password = getpass.getpass(L('Password: '))
    else:
        interactive = True

    is_service_principal = args.get('service-principal')
    tenant = args.get('tenant')

    profile = Profile()
    subscriptions = profile.find_subscriptions_on_login(
        interactive,
        username,
        password,
        is_service_principal,
        tenant)
    return list(subscriptions)
