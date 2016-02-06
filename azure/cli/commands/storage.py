import logging
from ..main import RC
from ..commands import CommandDispatcher

COMMAND_NAME = RC.STORAGE_COMMAND
COMMAND_HELP = RC.STORAGE_COMMAND_HELP

dispatch = CommandDispatcher('storage_command')

def add_commands(parser):
    dispatch.no_command = parser.print_help
    
    commands = parser.add_subparsers(title=RC.COMMANDS, dest=dispatch.command_name)
    
    cna = commands.add_parser('checkname', help="check the availability of an account name")
    cna.add_argument('--account_name', '-a', type=str, metavar=RC.NAME_METAVAR, required=True)

@dispatch
def checkname(args):
    '''Performs the 'checkname' command'''
    
    logging.info('''smc = StorageManagementClient(StorageManagementClientConfiguration())
smc.storage_accounts.check_name_availability({account_name!r})
'''.format_map(vars(args)))
