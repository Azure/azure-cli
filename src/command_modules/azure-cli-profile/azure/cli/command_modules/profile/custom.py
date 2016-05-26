# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use
#TODO: update adal-python to support it
#from azure.cli._debug import should_disable_connection_verify
from adal.adal_error import AdalError

from azure.cli._profile import Profile
from azure.cli._util import CLIError
import azure.cli._logging as _logging
from azure.cli._locale import L

logger = _logging.get_az_logger(__name__)

def list_subscriptions():
    '''List the imported subscriptions.'''
    profile = Profile()
    subscriptions = profile.load_cached_subscriptions()
    if not subscriptions:
        logger.warning('Please run "az login" to access your accounts.')
    return subscriptions

def set_active_subscription(subscription_name_or_id):
    '''Set the current subscription'''
    if not id:
        raise CLIError(L('Please provide subscription id or unique name.'))
    profile = Profile()
    profile.set_active_subscription(subscription_name_or_id)

def account_clear():
    '''Clear all stored subscriptions. To clear individual, use \'logout\''''
    profile = Profile()
    profile.logout_all()

def login(username=None, password=None, service_principal=None, tenant=None):
    '''Log in to an Azure subscription using Active Directory Organization Id'''
    interactive = False

    if username:
        if not password:
            import getpass
            password = getpass.getpass(L('Password: '))
    else:
        interactive = True

    profile = Profile()
    try:
        subscriptions = profile.find_subscriptions_on_login(
            interactive,
            username,
            password,
            service_principal,
            tenant)
    except AdalError as err:
        raise CLIError(err)
    return list(subscriptions)

def logout(username):
    '''Log out from Azure subscription using Active Directory.'''
    profile = Profile()
    profile.logout(username)
