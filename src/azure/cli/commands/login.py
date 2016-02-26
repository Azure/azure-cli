from msrest import Serializer
from msrestazure.azure_active_directory import UserPassCredentials
from azure.mgmt.resource.subscriptions import SubscriptionClient, \
                                              SubscriptionClientConfiguration

from .._profile import Profile
from ..commands import command, description, option
from .._debug import should_disable_connection_verify
from .._locale import L

CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'

@command('login')
@description(L('log in to an Azure subscription using Active Directory Organization Id'))
@option('--username -u <username>', L('organization Id. Microsoft Account is not yet supported.'))
@option('--password -p <password>', L('user password, will prompt if not given.'))
def login(args, unexpected): #pylint: disable=unused-argument
    username = args.get('username')

    password = args.get('password')
    if not password:
        import getpass
        password = getpass.getpass(L('Password: '))

    credentials = UserPassCredentials(username, 
                                      password, 
                                      client_id=CLIENT_ID, 
                                      verify=not should_disable_connection_verify())
    client = SubscriptionClient(SubscriptionClientConfiguration(credentials))
    subscriptions = client.subscriptions.list()

    if not subscriptions:
        raise RuntimeError(L('No subscriptions found for this account.'))

    serializable = Serializer().serialize_data(subscriptions, "[Subscription]")

    #keep useful properties and not json serializable 
    profile = Profile()
    consolidated = Profile.normalize_properties(username, subscriptions)
    profile.set_subscriptions(consolidated, credentials.token['access_token'])

    return serializable
