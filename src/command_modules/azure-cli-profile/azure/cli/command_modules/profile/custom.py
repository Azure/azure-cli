﻿#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use

from adal.adal_error import AdalError

from azure.cli._profile import Profile
from azure.cli._util import CLIError
import azure.cli._logging as _logging

logger = _logging.get_az_logger(__name__)

def load_subscriptions():
    profile = Profile()
    subscriptions = profile.load_cached_subscriptions()
    return subscriptions

def list_subscriptions():
    '''List the imported subscriptions.'''
    subscriptions = load_subscriptions()
    if not subscriptions:
        logger.warning('Please run "az login" to access your accounts.')
    return subscriptions

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
    '''Log in to an Azure subscription using Active Directory Organization Id'''
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
        raise CLIError(err)
    return list(subscriptions)

def logout(username=None):
    '''Log out from Azure subscription using Active Directory'''
    profile = Profile()
    if not username:
        username = profile.get_current_account_user()
    profile.logout(username)

def list_location():
    from azure.cli.commands.parameters import get_subscription_locations
    return get_subscription_locations()

