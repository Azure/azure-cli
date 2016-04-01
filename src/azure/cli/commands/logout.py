from .._profile import Profile
from ..commands import CommandTable
from .._locale import L

command_table = CommandTable()

@command_table.command('logout',
                       description=L('Log out from Azure subscription using Active Directory.'))
@command_table.option('--username -u',
                      help=L('User name used to log out from Azure Active Directory.'),
                      required=True)
def logout(args):
    profile = Profile()
    profile.logout(args['username'])
