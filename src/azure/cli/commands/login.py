import logging
from azure.cli.main import RC

COMMAND_NAME = 'login'
COMMAND_HELP = RC.LOGIN_COMMAND_HELP

def add_commands(parser):
    parser.add_argument('--user', '-u', metavar=RC.USERNAME_METAVAR)

def execute(args):
    user = args.user
    if not user:
        # TODO: move string to RC
        user = input('Enter username: ')
    
    # INFO: Deliberately delay imports for startup performance
    import getpass
    # TODO: move string to RC
    password = getpass.getpass('Enter password for {}: '.format(user))
    
    logging.info('''credentials = UserCredential({!r}, {!r})
'''.format(user, password))
