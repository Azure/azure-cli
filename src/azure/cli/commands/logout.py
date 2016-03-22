from .._profile import Profile
from ..commands import CommandTable
from .._locale import L

command_table = CommandTable()

def get_command_table():
    return command_table

#@command_table.description(L('Log out from Azure subscription using Active Directory.'))
@command_table.option('--username -u', dest='username', help=L('User name used to log out from Azure Active Directory.'))
@command_table.command('logout')
def logout(args, unexpected): #pylint: disable=unused-argument
    username = args.get('username')
    if not username:
        raise ValueError(L('Please provide a valid username to logout.'))

    profile = Profile()
    profile.logout(username)
