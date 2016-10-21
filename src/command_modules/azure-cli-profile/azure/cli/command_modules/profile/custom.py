#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use
import requests
from adal.adal_error import AdalError

from azure.cli.core._profile import Profile, CLOUD
from azure.cli.core._util import CLIError
import azure.cli.core._logging as _logging

logger = _logging.get_az_logger(__name__)

def load_subscriptions():
    profile = Profile()
    subscriptions = profile.load_cached_subscriptions()
    return subscriptions

def list_subscriptions(list_all=False): # pylint: disable=redefined-builtin
    '''List the imported subscriptions.'''
    subscriptions = load_subscriptions()
    if not subscriptions:
        logger.warning('Please run "az login" to access your accounts.')
    for sub in subscriptions:
        sub['cloudName'] = sub.pop('environmentName', None)
    return [sub for sub in subscriptions if list_all or sub['cloudName'] == CLOUD.name]

def set_active_subscription(subscription_name_or_id):
    '''Set the current subscription'''
    if not id:
        raise CLIError('Please provide subscription id or unique name.')
    profile = Profile()
    profile.set_active_subscription(subscription_name_or_id)

def account_clear():
    '''Clear all stored subscriptions. To clear individual, use \'logout\''''
    profile = Profile()
    profile.logout_all()

def login(username=None, password=None, service_principal=None, tenant=None):
    '''Log in to access Azure subscriptions'''
    interactive = False

    if username:
        if not password:
            import getpass
            password = getpass.getpass('Password: ')
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
        #try polish unfriendly server errors
        if username:
            msg = str(err)
            suggestion = "For cross-check, try 'az login' to authenticate through browser"
            if ('ID3242:' in msg) or ('Server returned an unknown AccountType' in msg):
                raise CLIError("The user name might be invalid. " + suggestion)
            if 'Server returned error in RSTR - ErrorCode' in msg:
                raise CLIError("Logging in through command line is not supported. " + suggestion)
        raise CLIError(err)
    except requests.exceptions.ConnectionError as err:
        raise CLIError('Please ensure you have network connection. Error detail: ' + str(err))
    all_subscriptions = list(subscriptions)
    for sub in all_subscriptions:
        sub['cloudName'] = sub.pop('environmentName', None)
    return all_subscriptions

def logout(username=None):
    '''Log out to remove accesses to Azure subscriptions'''
    profile = Profile()
    if not username:
        username = profile.get_current_account_user()
    profile.logout(username)

def list_locations():
    from azure.cli.core.commands.parameters import get_subscription_locations
    return get_subscription_locations()

