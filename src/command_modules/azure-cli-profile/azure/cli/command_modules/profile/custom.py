# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.prompting import prompt_pass, NoTTYException
import azure.cli.core.azlogging as azlogging
from azure.cli.core._profile import Profile
from azure.cli.core.util import CLIError

logger = azlogging.get_az_logger(__name__)


def load_subscriptions(all_clouds=False):
    profile = Profile()
    subscriptions = profile.load_cached_subscriptions(all_clouds)
    return subscriptions


def list_subscriptions(all=False):  # pylint: disable=redefined-builtin
    """List the imported subscriptions."""
    subscriptions = load_subscriptions(all_clouds=all)
    if not subscriptions:
        logger.warning('Please run "az login" to access your accounts.')
    for sub in subscriptions:
        sub['cloudName'] = sub.pop('environmentName', None)
    if not all:
        enabled_ones = [s for s in subscriptions if s['state'] == 'Enabled']
        if len(enabled_ones) != len(subscriptions):
            logger.warning("A few accounts are skipped as they don't have 'Enabled' state. "
                           "Use '--all' to display them.")
            subscriptions = enabled_ones
    return subscriptions


def show_subscription(subscription=None, expanded_view=None):
    profile = Profile()
    if not expanded_view:
        return profile.get_subscription(subscription)

    logger.warning("'--expanded-view' is deprecating and will be removed in a future release. You can get the same "
                   "information using 'az cloud show'")
    return profile.get_expanded_subscription_info(subscription)


def get_access_token(subscription=None, resource=None):
    '''
    get AAD token to access to a specified resource
    :param resource: Azure resource endpoints. Default to Azure Resource Manager
    Use 'az cloud show' command for other Azure resources
    '''
    profile = Profile()
    creds, subscription, tenant = profile.get_raw_token(subscription=subscription,
                                                        resource=resource)
    return {
        'tokenType': creds[0],
        'accessToken': creds[1],
        'expiresOn': creds[2]['expiresOn'],
        'subscription': subscription,
        'tenant': tenant
    }


def set_active_subscription(subscription):
    """Set the current subscription"""
    if not id:
        raise CLIError('Please provide subscription id or unique name.')
    profile = Profile()
    profile.set_active_subscription(subscription)


def account_clear():
    """Clear all stored subscriptions. To clear individual, use 'logout'"""
    profile = Profile()
    profile.logout_all()


def login(username=None, password=None, service_principal=None, tenant=None,
          allow_no_subscriptions=False):
    """Log in to access Azure subscriptions"""
    from adal.adal_error import AdalError
    import requests
    interactive = False

    if username:
        if not password:
            try:
                password = prompt_pass('Password: ')
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')
    else:
        interactive = True

    profile = Profile()
    try:
        subscriptions = profile.find_subscriptions_on_login(
            interactive,
            username,
            password,
            service_principal,
            tenant,
            allow_no_subscriptions=allow_no_subscriptions)
    except AdalError as err:
        # try polish unfriendly server errors
        if username:
            msg = str(err)
            suggestion = "For cross-check, try 'az login' to authenticate through browser."
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
    """Log out to remove access to Azure subscriptions"""
    profile = Profile()
    if not username:
        username = profile.get_current_account_user()
    profile.logout(username)


def list_locations():
    from azure.cli.core.commands.parameters import get_subscription_locations
    return get_subscription_locations()
