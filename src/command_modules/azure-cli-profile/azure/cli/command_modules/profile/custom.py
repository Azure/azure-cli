# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from azure.cli.core.prompting import prompt_pass, NoTTYException
from azure.cli.core import get_az_logger
from azure.cli.core._profile import Profile
from azure.cli.core.util import CLIError, in_cloud_console
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.commands.validators import DefaultStr

logger = get_az_logger(__name__)

_CLOUD_CONSOLE_WARNING_TEMPLATE = ("Azure Cloud Shell automatically authenticates the user account it was initially"
                                   " launched under, as a result 'az %s' is disabled.")


def load_subscriptions(all_clouds=False, refresh=False):
    profile = Profile()
    if refresh:
        subscriptions = profile.refresh_accounts()
    subscriptions = profile.load_cached_subscriptions(all_clouds)
    return subscriptions


def list_subscriptions(all=False, refresh=False):  # pylint: disable=redefined-builtin
    """List the imported subscriptions."""
    subscriptions = load_subscriptions(all_clouds=all, refresh=refresh)
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


def show_subscription(subscription=None, show_auth_for_sdk=None):
    import json
    profile = Profile()
    if not show_auth_for_sdk:
        return profile.get_subscription(subscription)

    # sdk-auth file should be in json format all the time, hence the print
    print(json.dumps(profile.get_sp_auth_info(subscription), indent=2))


def get_access_token(subscription=None, resource=None):
    '''
    get AAD token to access to a specified resource
    :param resource: Azure resource endpoints. Default to Azure Resource Manager
    Use 'az cloud show' command for other Azure resources
    '''
    resource = (resource or get_active_cloud().endpoints.active_directory_resource_id)
    profile = Profile()
    creds, subscription, tenant = profile.get_raw_token(resource, subscription=subscription)
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
          allow_no_subscriptions=False, msi=False, msi_port=DefaultStr(50342)):
    """Log in to access Azure subscriptions"""
    import os
    import re
    from adal.adal_error import AdalError
    import requests

    # quick argument usage check
    if (any([username, password, service_principal, tenant, allow_no_subscriptions]) and
            any([msi, not getattr(msi_port, 'is_default', None)])):
        raise CLIError("usage error: '--msi/--msi-port' are not applicable with other arguments")

    interactive = False

    profile = Profile()

    if in_cloud_console():
        console_tokens = os.environ.get('AZURE_CONSOLE_TOKENS', None)
        if console_tokens:
            return profile.find_subscriptions_in_cloud_console(re.split(';|,', console_tokens))
        logger.warning(_CLOUD_CONSOLE_WARNING_TEMPLATE, 'login')
        return

    if msi:
        return profile.find_subscriptions_in_vm_with_msi(msi_port)

    if username:
        if not password:
            try:
                password = prompt_pass('Password: ')
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')
    else:
        interactive = True

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
    if in_cloud_console():
        logger.warning(_CLOUD_CONSOLE_WARNING_TEMPLATE, 'logout')
        return

    profile = Profile()
    if not username:
        username = profile.get_current_account_user()
    profile.logout(username)


def list_locations():
    from azure.cli.core.commands.parameters import get_subscription_locations
    return get_subscription_locations()
