import logging
from ..main import RC
from ..commands import CommandDispatcher

COMMAND_NAME = 'storage'
COMMAND_HELP = RC.STORAGE_COMMAND_HELP

dispatch = CommandDispatcher('storage_command')

def add_commands(parser):
    dispatch.no_command = parser.print_help
    
    # INFO: Since "storage" has subcommands, we need to add subparsers
    # Each subcommand is added to `commands` using `add_parser`
    commands = parser.add_subparsers(title=RC.COMMANDS, dest=dispatch.command_name)
    
    # TODO: move help string to RC
    cna = commands.add_parser('checkname', help="check the availability of an account name")
    cna.add_argument('--account_name', '-a', type=str, metavar=RC.NAME_METAVAR, required=True)

# INFO: Applying @dispatch enables the processor to call directly into this function
# If the function name does not match the command, use @dispatch("command")
@dispatch
def checkname(args):
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    
    logging.info('''smc = StorageManagementClient(StorageManagementClientConfiguration())
smc.storage_accounts.check_name_availability({account_name!r})
'''.format_map(vars(args)))
    
    smc = StorageManagementClient(StorageManagementClientConfiguration())
    logging.warn(smc.storage_accounts.check_name_availability(args.account_name))
    
    
