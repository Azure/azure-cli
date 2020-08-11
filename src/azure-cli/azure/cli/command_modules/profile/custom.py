# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from knack.log import get_logger
from knack.prompting import prompt_pass, NoTTYException
from knack.util import CLIError

from azure.cli.core._profile import Profile
from azure.cli.core.util import in_cloud_console

logger = get_logger(__name__)

cloud_resource_type_mappings = {
    "oss-rdbms": "ossrdbms_resource_id",
    "arm": "active_directory_resource_id",
    "aad-graph": "active_directory_graph_resource_id",
    "ms-graph": "microsoft_graph_resource_id",
    "batch": "batch_resource_id",
    "media": "media_resource_id",
    "data-lake": "active_directory_data_lake_resource_id"
}

_CLOUD_CONSOLE_LOGOUT_WARNING = ("Logout successful. Re-login to your initial Cloud Shell identity with"
                                 " 'az login --identity'. Login with a new identity with 'az login'.")
_CLOUD_CONSOLE_LOGIN_WARNING = ("Cloud Shell is automatically authenticated under the initial account signed-in with."
                                " Run 'az login' only if you need to use a different account")


def list_subscriptions(cmd, all=False, refresh=False):  # pylint: disable=redefined-builtin
    """List the imported subscriptions."""
    from azure.cli.core.api import load_subscriptions

    subscriptions = load_subscriptions(cmd.cli_ctx, all_clouds=all, refresh=refresh)
    if not subscriptions:
        logger.warning('Please run "az login" to access your accounts.')
    for sub in subscriptions:
        sub['cloudName'] = sub.pop('environmentName', None)
    if not all:
        enabled_ones = [s for s in subscriptions if s.get('state') == 'Enabled']
        if len(enabled_ones) != len(subscriptions):
            logger.warning("A few accounts are skipped as they don't have 'Enabled' state. "
                           "Use '--all' to display them.")
            subscriptions = enabled_ones
    return subscriptions


# pylint: disable=inconsistent-return-statements
def show_subscription(cmd, subscription=None, show_auth_for_sdk=None):
    import json
    profile = Profile(cli_ctx=cmd.cli_ctx)
    if not show_auth_for_sdk:
        return profile.get_subscription(subscription)

    # sdk-auth file should be in json format all the time, hence the print
    print(json.dumps(profile.get_sp_auth_info(subscription), indent=2))


def get_access_token(cmd, subscription=None, resource=None, scopes=None, resource_type=None, tenant=None):
    """
    get AAD token to access to a specified resource.
    Use 'az cloud show' command for other Azure resources
    """
    if resource is None and resource_type is not None:
        endpoints_attr_name = cloud_resource_type_mappings[resource_type]
        resource = getattr(cmd.cli_ctx.cloud.endpoints, endpoints_attr_name)

    if resource and scopes:
        raise CLIError("resource and scopes can't be provided at the same time.")

    resource = (resource or cmd.cli_ctx.cloud.endpoints.active_directory_resource_id)

    profile = Profile(cli_ctx=cmd.cli_ctx)
    creds, subscription, tenant = profile.get_raw_token(subscription=subscription, resource=resource, scopes=scopes,
                                                        tenant=tenant)

    token_entry = creds[2]
    # MSIAuthentication's token entry has `expires_on`, while ADAL's token entry has `expiresOn`
    # Unify to ISO `expiresOn`, like "2020-06-30 06:14:41"
    if 'expires_on' in token_entry:
        from datetime import datetime
        # https://docs.python.org/3.8/library/datetime.html#strftime-and-strptime-format-codes
        token_entry['expiresOn'] = datetime.fromtimestamp(int(token_entry['expires_on']))\
            .strftime("%Y-%m-%d %H:%M:%S.%f")

    result = {
        'tokenType': creds[0],
        'accessToken': creds[1],
        'expiresOn': creds[2].get('expiresOn', 'N/A'),
        'tenant': tenant
    }
    if subscription:
        result['subscription'] = subscription
    return result


def set_active_subscription(cmd, subscription):
    """Set the current subscription"""
    profile = Profile(cli_ctx=cmd.cli_ctx)
    if not id:
        raise CLIError('Please provide subscription id or unique name.')
    profile.set_active_subscription(subscription)


def account_clear(cmd, clear_credential=False):
    """Clear all stored subscriptions. To clear individual, use 'logout'"""
    if in_cloud_console():
        logger.warning(_CLOUD_CONSOLE_LOGOUT_WARNING)
    profile = Profile(cli_ctx=cmd.cli_ctx)
    profile.logout_all(clear_credential)


# pylint: disable=inconsistent-return-statements, too-many-branches
def login(cmd, username=None, password=None, service_principal=None, tenant=None, allow_no_subscriptions=False,
          identity=False, use_device_code=False, use_cert_sn_issuer=None, tenant_access=False, environment=False):
    """Log in to access Azure subscriptions"""
    from adal.adal_error import AdalError
    import requests

    # quick argument usage check
    if any([password, service_principal, tenant]) and identity:
        raise CLIError("usage error: '--identity' is not applicable with other arguments")
    if any([password, service_principal, username, identity]) and use_device_code:
        raise CLIError("usage error: '--use-device-code' is not applicable with other arguments")
    if any([password, service_principal, username, identity, use_device_code]) and environment:
        raise CLIError("usage error: '--environment' is not applicable with other arguments")
    if use_cert_sn_issuer and not service_principal:
        raise CLIError("usage error: '--use-sn-issuer' is only applicable with a service principal")
    if service_principal and not username:
        raise CLIError('usage error: --service-principal --username NAME --password SECRET --tenant TENANT')

    interactive = False

    profile = Profile(cli_ctx=cmd.cli_ctx, async_persist=False)

    if identity:
        if in_cloud_console():
            return profile.login_in_cloud_shell()
        return profile.login_with_managed_identity(username, allow_no_subscriptions)
    if in_cloud_console():  # tell users they might not need login
        logger.warning(_CLOUD_CONSOLE_LOGIN_WARNING)

    if username:
        if not password:
            try:
                password = prompt_pass('Password: ')
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')
    else:
        interactive = True

    if environment:
        return profile.login_with_environment_credential(find_subscriptions=not tenant_access)

    try:
        subscriptions = profile.login(
            interactive,
            username,
            password,
            service_principal,
            tenant,
            use_device_code=use_device_code,
            allow_no_subscriptions=allow_no_subscriptions,
            use_cert_sn_issuer=use_cert_sn_issuer, find_subscriptions=not tenant_access)
    except AdalError as err:
        # try polish unfriendly server errors
        if username:
            msg = str(err)
            suggestion = "For cross-check, try 'az login' to authenticate through browser."
            if ('ID3242:' in msg) or ('Server returned an unknown AccountType' in msg):
                raise CLIError("The user name might be invalid. " + suggestion)
            if 'Server returned error in RSTR - ErrorCode' in msg:
                raise CLIError("Logging in through command line is not supported. " + suggestion)
            if 'wstrust' in msg:
                raise CLIError("Authentication failed due to error of '" + msg + "' "
                               "This typically happens when attempting a Microsoft account, which requires "
                               "interactive login. Please invoke 'az login' to cross check. "
                               # pylint: disable=line-too-long
                               "More details are available at https://github.com/AzureAD/microsoft-authentication-library-for-python/wiki/Username-Password-Authentication")
        raise CLIError(err)
    except requests.exceptions.SSLError as err:
        from azure.cli.core.util import SSLERROR_TEMPLATE
        raise CLIError(SSLERROR_TEMPLATE.format(str(err)))
    except requests.exceptions.ConnectionError as err:
        raise CLIError('Please ensure you have network connection. Error detail: ' + str(err))
    all_subscriptions = list(subscriptions)
    for sub in all_subscriptions:
        sub['cloudName'] = sub.pop('environmentName', None)
    return all_subscriptions


def logout(cmd, username=None, clear_credential=False):
    """Log out to remove access to Azure subscriptions"""
    if in_cloud_console():
        logger.warning(_CLOUD_CONSOLE_LOGOUT_WARNING)

    profile = Profile(cli_ctx=cmd.cli_ctx)
    if not username:
        username = profile.get_current_account_user()
    profile.logout(username, clear_credential)


def list_locations(cmd):
    from azure.cli.core.commands.parameters import get_subscription_locations
    return get_subscription_locations(cmd.cli_ctx)


def check_cli(cmd):
    from azure.cli.core.file_util import (
        create_invoker_and_load_cmds_and_args, get_all_help)

    exceptions = {}

    print('Running CLI self-test.\n')

    print('Loading all commands and arguments...')
    try:
        create_invoker_and_load_cmds_and_args(cmd.cli_ctx)
        print('Commands loaded OK.\n')
    except Exception as ex:  # pylint: disable=broad-except
        exceptions['load_commands'] = ex
        logger.error('Error occurred loading commands!\n')
        raise ex

    print('Retrieving all help...')
    try:
        get_all_help(cmd.cli_ctx, skip=False)
        print('Help loaded OK.\n')
    except Exception as ex:  # pylint: disable=broad-except
        exceptions['load_help'] = ex
        logger.error('Error occurred loading help!\n')
        raise ex

    if not exceptions:
        print('CLI self-test completed: OK')
    else:
        raise CLIError(exceptions)
