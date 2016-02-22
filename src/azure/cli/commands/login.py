from azure.mgmt.resource.subscriptions import SubscriptionClient, \
                                              SubscriptionClientConfiguration
from msrestazure.azure_active_directory import UserPassCredentials

from .._logging import logging
from .._util import TableOutput
from ..commands import command, description, option
import azure.cli._profile as profile

CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'

@command('login')
@description('log in to an Azure subscription using Active Directory Organization Id')
@option('--username -u <username>', _('organization Id. Microsoft Account is not yet supported.'))
@option('--password -p <password>', _('user password, will prompt if not given.'))
def login(args, unexpected):
    username = args.get('username')

    password = args.get('password')
    if not password:
        import getpass
        password = getpass.getpass(_('Password: '))

    credentials = UserPassCredentials(username, password, client_id=CLIENT_ID)
    profile.set_access_token(credentials.token['access_token'])
    client = SubscriptionClient(SubscriptionClientConfiguration(credentials))
    subscriptions = client.subscriptions.list()

    if not subscriptions:
        raise RuntimeError(_("No subscriptions found for this account"))

    #keep useful properties and not json serializable 
    consolidated = []
    for s in subscriptions:
        subscription = {};
        subscription['id'] = s.id.split('/')[-1]
        subscription['name'] = s.display_name
        subscription['state'] = s.state
        subscription['user'] = username
        subscription['active'] = False
        consolidated.append(subscription)

    profile.set_subscriptions(consolidated, consolidated[0])

    #TODO, replace with JSON display
    with TableOutput() as to:
        for subscription in profile.get_subscriptions():
            to.cell('Name', subscription['name'])
            to.cell('Active', bool(subscription['active']))
            to.cell('User', subscription['user'])
            to.cell('Subscription Id', subscription['id'])
            to.cell('State', subscription['state'])
            to.end_row()
