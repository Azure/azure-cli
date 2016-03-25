from .._profile import Profile
from ..commands import CommandTable
from .._locale import L

command_table = CommandTable()

def get_command_table():
    return command_table

@command_table.option('--username -u', help=L('User name used to log out from Azure Active Directory.'),
                      required=True)
@command_table.command('logout', description=L('Log out from Azure subscription using Active Directory.'))
def logout(args, unexpected): #pylint: disable=unused-argument
    profile = Profile()
    profile.logout(args['username'])
