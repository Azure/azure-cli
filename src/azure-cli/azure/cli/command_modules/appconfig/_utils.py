from __future__ import print_function

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from knack.log import get_logger
from knack.prompting import NoTTYException, prompt_y_n
from knack.util import CLIError
from azure.appconfiguration import AzureAppConfigurationClient
from azure.mgmt.appconfiguration.models import ErrorException

from ._client_factory import cf_configstore
from ._constants import HttpHeaders

logger = get_logger(__name__)


def construct_connection_string(cmd, config_store_name):
    connection_string_template = 'Endpoint={};Id={};Secret={}'
    # If the logged in user/Service Principal does not have 'Reader' or 'Contributor' role
    # assigned for the requested AppConfig, resolve_resource_group will raise CLI error
    resource_group_name, endpoint = resolve_resource_group(cmd, config_store_name)

    try:
        config_store_client = cf_configstore(cmd.cli_ctx)
        access_keys = config_store_client.list_keys(
            resource_group_name, config_store_name)
        for entry in access_keys:
            if not entry.read_only:
                return connection_string_template.format(endpoint, entry.id, entry.value)
    except Exception as ex:
        raise CLIError(
            'Failed to get access keys for the App Configuration "{}". Make sure that the account that logged in has "Contributor" role assigned for this App Configuration store.\n{}'.format(config_store_name, str(ex)))

    raise CLIError('Cannot find a read write access key for the App Configuration {}'.format(
        config_store_name))


def resolve_resource_group(cmd, config_store_name):
    try:
        config_store_client = cf_configstore(cmd.cli_ctx)
        all_stores = config_store_client.list()
        for store in all_stores:
            if store.name.lower() == config_store_name.lower():
                # Id has a fixed structure /subscriptions/subscriptionName/resourceGroups/groupName/providers/providerName/configurationStores/storeName"
                return store.id.split('/')[4], store.endpoint
    except ErrorException as ex:
        raise CLIError("Failed to get the list of App Configuration stores for the current user. Make sure that the account that logged in has 'Reader' or 'Contributor' role assigned for the required App Configuration store.\n{}".format(str(ex)))

    raise CLIError("Failed to find the App Configuration store '{}'. Make sure that the account that logged in has 'Reader' or 'Contributor' role assigned for this App Configuration store.".format(config_store_name))


def user_confirmation(message, yes=False):
    if yes:
        return
    try:
        if not prompt_y_n(message):
            raise CLIError('Operation cancelled.')
    except NoTTYException:
        raise CLIError(
            'Unable to prompt for confirmation as no tty available. Use --yes.')


def resolve_connection_string(cmd, config_store_name=None, connection_string=None):
    string = ''
    error_message = '''You may have specified both store name and connection string, which is a conflict.
Please specify exactly ONE (suggest connection string) in one of the following options:\n
1 pass in App Configuration store name as a parameter\n
2 pass in connection string as a parameter\n
3 preset App Configuration store name using 'az configure --defaults app_configuration_store=xxxx'\n
4 preset connection string using 'az configure --defaults appconfig_connection_string=xxxx'\n
5 preset connection in environment variable like set AZURE_APPCONFIG_CONNECTION_STRING=xxxx'''

    if config_store_name:
        string = construct_connection_string(cmd, config_store_name)

    if connection_string:
        if string and ';'.join(sorted(connection_string.split(';'))) != string:
            raise CLIError(error_message)
        string = connection_string

    connection_string_env = cmd.cli_ctx.config.get(
        'appconfig', 'connection_string', None)

    if connection_string_env:
        if not is_valid_connection_string(connection_string_env):
            raise CLIError(
                "The environment variable connection string is invalid. Correct format should be Endpoint=https://example.appconfig.io;Id=xxxxx;Secret=xxxx")

        if string and ';'.join(sorted(connection_string_env.split(';'))) != string:
            raise CLIError(error_message)
        string = connection_string_env

    if not string:
        raise CLIError(
            'If you are using "key" auth mode, please specify config store name or connection string(suggested).')
    return string


def is_valid_connection_string(connection_string):
    if connection_string is not None:
        segments = connection_string.split(';')
        if len(segments) != 3:
            return False

        segments.sort()
        if segments[0].startswith('Endpoint=') and segments[1].startswith('Id=') and segments[2].startswith('Secret='):
            return True
    return False


def get_store_name_from_connection_string(connection_string):
    if is_valid_connection_string(connection_string):
        segments = dict(seg.split("=", 1) for seg in connection_string.split(";"))
        endpoint = segments.get("Endpoint")
        if endpoint:
            return endpoint.split("//")[1].split('.')[0]
    return None


def prep_null_label_for_url_encoding(label=None):
    if label is not None:
        import ast
        # ast library requires quotes around string
        label = '"{0}"'.format(label)
        label = ast.literal_eval(label)
    return label


def get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint):
    azconfig_client = None
    if auth_mode == "key":
        connection_string = resolve_connection_string(cmd, name, connection_string)
        azconfig_client = AzureAppConfigurationClient.from_connection_string(connection_string=connection_string,
                                                                             user_agent=HttpHeaders.USER_AGENT)
    if auth_mode == "login":
        if not endpoint:
            try:
                if name:
                    _, endpoint = resolve_resource_group(cmd, name)
                else:
                    raise CLIError("App Configuration endpoint or name should be provided if auth mode is 'login'.")
            except Exception as ex:
                raise CLIError("Failed to retrieve App Configuration endpoint from store name.\n" + str(ex))

        from azure.cli.core._profile import Profile
        profile = Profile(cli_ctx=cmd.cli_ctx)
        # Due to this bug in get_login_credentials: https://github.com/Azure/azure-cli/issues/15179,
        # we need to manage the AAD scope by passing appconfig endpoint as resource
        cred, _, _ = profile.get_login_credentials(resource=endpoint)
        azconfig_client = AzureAppConfigurationClient(credential=cred,
                                                      base_url=endpoint,
                                                      user_agent=HttpHeaders.USER_AGENT)

    if not azconfig_client:
        raise CLIError("Could not get App Configuration client due to insufficient permissions.")

    return azconfig_client
