import logging
from azure.cli.main import RC

COMMAND_NAME = 'login'
COMMAND_HELP = 'helps you log in'

def add_commands(parser):
    parser.add_argument('--user', '-u', metavar=RC.USERNAME_METAVAR)

def execute(args):
    '''Performs the 'login' command.'''
    
    user = args.user
    if not user:
        user = input('Enter username: ')
    
    import getpass
    password = getpass.getpass('Enter password for {}: '.format(user))
    
    logging.info('''credentials = UserCredential({!r}, {!r})
'''.format(user, password))
