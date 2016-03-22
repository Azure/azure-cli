from msrestazure.azure_active_directory import UserPassCredentials, ServicePrincipalCredentials
from azure.mgmt.resource.subscriptions import (SubscriptionClient,
                                               SubscriptionClientConfiguration)

from .._profile import Profile
from ..commands import CommandTable
from .._debug import should_disable_connection_verify
from .._locale import L

CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'

command_table = CommandTable()

def get_command_table():
    return command_table


@command_table.option('--username -u', dest='username', required=True, 
                      help=L('organization Id or service principal. Microsoft Account is not yet supported.'))
@command_table.option('--password -p', help=L('user password or client secret, will prompt if not given.'))
@command_table.option('--service-principal', help=L('the credential represents a service principal.'))
@command_table.option('--tenant -t', help=L('the tenant associated with the service principal.'))
@command_table.command('login', description=L('log in to an Azure subscription using Active Directory Organization Id'))
def login(args, unexpected): #pylint: disable=unused-argument
    username = args.get('username')

    password = args.get('password')
    if not password:
        import getpass
        password = getpass.getpass(L('Password: '))

    cert_verify = not should_disable_connection_verify()
    if args.get('service-principal'):
        tenant = args.get('tenant')
        if not tenant:
            raise ValueError(L('Please supply tenant using "--tenant"'))

        credentials = ServicePrincipalCredentials(username,
                                                  password,
                                                  tenant=tenant,
                                                  verify=cert_verify)
    else:
        credentials = UserPassCredentials(username, #pylint: disable=redefined-variable-type
                                          password,
                                          client_id=CLIENT_ID,
                                          verify=cert_verify)

    client = SubscriptionClient(SubscriptionClientConfiguration(credentials))
    subscriptions = client.subscriptions.list()

    if not subscriptions:
        raise RuntimeError(L('No subscriptions found for this account.'))

    #keep useful properties and not json serializable
    profile = Profile()
    consolidated = Profile.normalize_properties(username, subscriptions)
    profile.set_subscriptions(consolidated, credentials.token['access_token'])

    return list(subscriptions)
