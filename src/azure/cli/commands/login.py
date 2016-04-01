from __future__ import print_function
from msrest.authentication import BasicTokenAuthentication
from adal import (acquire_token_with_username_password,
                  acquire_token_with_client_credentials,
                  acquire_user_code,
                  acquire_token_with_device_code)
from azure.mgmt.resource.subscriptions import (SubscriptionClient,
                                               SubscriptionClientConfiguration)

from .._profile import Profile
from ..commands import CommandTable
#TODO: update adal-python to support it
#from .._debug import should_disable_connection_verify
from .._locale import L

command_table = CommandTable()

@command_table.command('login')
@command_table.description(L('log in to an Azure subscription using Active Directory Organization Id')) # pylint: disable=line-too-long
@command_table.option('--username -u',
                      help=L('organization Id or service principal. Microsoft Account is not yet supported.')) # pylint: disable=line-too-long
@command_table.option('--password -p',
                      help=L('user password or client secret, will prompt if not given.'))
@command_table.option('--service-principal',
                      help=L('the credential represents a service principal.'))
@command_table.option('--tenant -t', help=L('the tenant associated with the service principal.'))
def login(args):
    interactive = False

    username = args.get('username')
    if username:
        password = args.get('password')
        if not password:
            import getpass
            password = getpass.getpass(L('Password: '))
    else:
        interactive = True

    tenant = args.get('tenant')
    authority = _get_authority_url(tenant)
    if interactive:
        user_code = acquire_user_code(authority)
        print(user_code['message'])
        credentials = acquire_token_with_device_code(authority, user_code)
        username = credentials['userId']
    else:
        if args.get('service-principal'):
            if not tenant:
                raise ValueError(L('Please supply tenant using "--tenant"'))

            credentials = acquire_token_with_client_credentials(
                authority,
                username,
                password)
        else:
            credentials = acquire_token_with_username_password(
                authority,
                username,
                password)

    token_credential = BasicTokenAuthentication({'access_token': credentials['accessToken']})
    client = SubscriptionClient(SubscriptionClientConfiguration(token_credential))
    subscriptions = client.subscriptions.list()

    if not subscriptions:
        raise RuntimeError(L('No subscriptions found for this account.'))

    #keep useful properties and not json serializable
    profile = Profile()
    consolidated = Profile.normalize_properties(username, subscriptions)
    profile.set_subscriptions(consolidated, credentials['accessToken'])

    return list(subscriptions)

def _get_authority_url(tenant=None):
    return 'https://login.microsoftonline.com/{}'.format(tenant or 'common')
