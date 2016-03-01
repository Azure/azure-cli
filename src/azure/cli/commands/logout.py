from .._profile import Profile
from ..commands import command, description, option
from .._locale import L

@command('logout')
@description(L('Log out from Azure subscription using Active Directory.'))
@option('--username -u <username>', L('User name used to log out from Azure Active Directory.'))
def logout(args, unexpected): #pylint: disable=unused-argument
    username = args.get('username')
    if not username:
        raise ValueError(L('Please provide a valid username to logout.'))

    profile = Profile()
    profile.logout(username)
