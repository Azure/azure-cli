# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys

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


LOGIN_ANNOUNCEMENT = (
    "[Announcements]\n"
    "With the new Azure CLI login experience, you can select the subscription you want to use more easily. "
    "Learn more about it and its configuration at https://go.microsoft.com/fwlink/?linkid=2271236\n\n"
    "If you encounter any problem, please open an issue at https://aka.ms/azclibug\n")

LOGIN_OUTPUT_WARNING = (
    "[Warning] The login output has been updated. Please be aware that it no longer displays the full list of "
    "available subscriptions by default.\n")

USERNAME_PASSWORD_DEPRECATION_WARNING_AZURE_CLOUD = (
    "Starting September 1, 2025, MFA will be gradually enforced for Azure public cloud. "
    "The authentication with username and password in the command line is not supported with MFA. "
    "Consider using one of the compatible authentication methods. "
    "For more details, see https://go.microsoft.com/fwlink/?linkid=2276314")

USERNAME_PASSWORD_DEPRECATION_WARNING_OTHER_CLOUD = (
    "Using authentication with username and password in the command line is strongly discouraged. "
    "Consider using one of the recommended authentication methods. "
    "For more details, see https://go.microsoft.com/fwlink/?linkid=2276314")


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


def show_subscription(cmd, subscription=None):
    profile = Profile(cli_ctx=cmd.cli_ctx)
    return profile.get_subscription(subscription)


def get_access_token(cmd, subscription=None, resource=None, scopes=None, resource_type=None, tenant=None):
    """
    get AAD token to access to a specified resource.
    Use 'az cloud show' command for other Azure resources
    """
    if resource is None and resource_type:
        endpoints_attr_name = cloud_resource_type_mappings[resource_type]
        resource = getattr(cmd.cli_ctx.cloud.endpoints, endpoints_attr_name)

    profile = Profile(cli_ctx=cmd.cli_ctx)
    creds, subscription, tenant = profile.get_raw_token(subscription=subscription, resource=resource, scopes=scopes,
                                                        tenant=tenant)

    result = {
        'tokenType': creds[0],
        'accessToken': creds[1],
        'expires_on': creds[2]['expires_on'],
        'expiresOn': creds[2]['expiresOn'],
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


def account_clear(cmd):
    """Clear all stored subscriptions. To clear individual, use 'logout'"""
    _remove_adal_token_cache()

    if in_cloud_console():
        logger.warning(_CLOUD_CONSOLE_LOGOUT_WARNING)
    profile = Profile(cli_ctx=cmd.cli_ctx)
    profile.logout_all()


# pylint: disable=too-many-branches, too-many-locals
def login(cmd, username=None, password=None, tenant=None, scopes=None, allow_no_subscriptions=False,
          claims_challenge=None,
          # Device code flow
          use_device_code=False,
          # Service principal
          service_principal=None, certificate=None, use_cert_sn_issuer=None, client_assertion=None,
          # Managed identity
          identity=False, client_id=None, object_id=None, resource_id=None):
    """Log in to access Azure subscriptions"""

    # quick argument usage check
    if any([password, service_principal, tenant]) and identity:
        raise CLIError("usage error: '--identity' is not applicable with other arguments")
    if identity and username:
        raise CLIError('Passing the managed identity ID with --username is no longer supported. '
                       'Use --client-id, --object-id or --resource-id instead.')
    if any([password, service_principal, username, identity]) and use_device_code:
        raise CLIError("usage error: '--use-device-code' is not applicable with other arguments")
    if use_cert_sn_issuer and not service_principal:
        raise CLIError("usage error: '--use-sn-issuer' is only applicable with a service principal")
    if service_principal and not username:
        raise CLIError('usage error: --service-principal --username NAME --password SECRET --tenant TENANT')
    if username and not service_principal and not identity:
        if cmd.cli_ctx.cloud.endpoints.active_directory.startswith('https://login.microsoftonline.com'):
            logger.warning(USERNAME_PASSWORD_DEPRECATION_WARNING_AZURE_CLOUD)
        else:
            logger.warning(USERNAME_PASSWORD_DEPRECATION_WARNING_OTHER_CLOUD)

    if claims_challenge:
        from azure.cli.core.util import b64decode
        claims_challenge = b64decode(claims_challenge)

    interactive = False

    profile = Profile(cli_ctx=cmd.cli_ctx)

    if identity:
        if in_cloud_console():
            return profile.login_in_cloud_shell()
        return profile.login_with_managed_identity(
            client_id=client_id, object_id=object_id, resource_id=resource_id,
            allow_no_subscriptions=allow_no_subscriptions)
    if in_cloud_console():  # tell users they might not need login
        logger.warning(_CLOUD_CONSOLE_LOGIN_WARNING)

    if username:
        if not (password or client_assertion or certificate):
            try:
                password = prompt_pass('Password: ')
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')
    else:
        interactive = True

    if service_principal:
        from azure.cli.core.auth.identity import ServicePrincipalAuth
        password = ServicePrincipalAuth.build_credential(
            client_secret=password,
            certificate=certificate, use_cert_sn_issuer=use_cert_sn_issuer,
            client_assertion=client_assertion)

    login_experience_v2 = cmd.cli_ctx.config.getboolean('core', 'login_experience_v2', fallback=True)
    # Send login_experience_v2 config to telemetry
    from azure.cli.core.telemetry import set_login_experience_v2
    set_login_experience_v2(login_experience_v2)

    select_subscription = interactive and sys.stdin.isatty() and sys.stdout.isatty() and login_experience_v2

    subscriptions = profile.login(
        interactive,
        username,
        password,
        service_principal,
        tenant,
        scopes=scopes,
        use_device_code=use_device_code,
        allow_no_subscriptions=allow_no_subscriptions,
        use_cert_sn_issuer=use_cert_sn_issuer,
        show_progress=select_subscription,
        claims_challenge=claims_challenge
    )

    # Launch interactive account selection. No JSON output.
    if select_subscription:
        from ._subscription_selector import SubscriptionSelector
        from azure.cli.core._profile import _SUBSCRIPTION_ID

        selected = SubscriptionSelector(subscriptions)()
        profile.set_active_subscription(selected[_SUBSCRIPTION_ID])

        print(LOGIN_ANNOUNCEMENT)
        logger.warning(LOGIN_OUTPUT_WARNING)
        return

    all_subscriptions = list(subscriptions)
    for sub in all_subscriptions:
        sub['cloudName'] = sub.pop('environmentName', None)
    return all_subscriptions


def logout(cmd, username=None):
    """Log out to remove access to Azure subscriptions"""
    _remove_adal_token_cache()

    if in_cloud_console():
        logger.warning(_CLOUD_CONSOLE_LOGOUT_WARNING)

    profile = Profile(cli_ctx=cmd.cli_ctx)
    if not username:
        username = profile.get_current_account_user()
    profile.logout(username)


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


def _remove_adal_token_cache():
    """Remove ADAL token cache file ~/.azure/accessTokens.json, as it is no longer needed by MSAL-based Azure CLI.
    """
    from azure.cli.core._environment import get_config_dir
    adal_token_cache = os.path.join(get_config_dir(), 'accessTokens.json')
    try:
        os.remove(adal_token_cache)
        return True  # Deleted
    except FileNotFoundError:
        return False  # Not exist
