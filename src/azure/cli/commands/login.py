import logging
from ..main import RC, CONFIG, SESSION
from ..commands import command

def add_commands(parser):
    parser.add_argument('--user', '-u', metavar=RC.USERNAME_METAVAR)

@command('login --user <username>')
def login(args):
    user = args.get('user') or SESSION.get('user') or CONFIG.get('user')
    if not user:
        user = input(RC.ENTER_USERNAME)
    
    import getpass
    password = getpass.getpass(RC.ENTER_PASSWORD_FOR.format(user))
    
    logging.info('''credentials = UserCredential({!r}, {!r})
'''.format(user, password))

    # TODO: get and cache token rather than user/password
    SESSION['user'] = user
    SESSION['password'] = password
