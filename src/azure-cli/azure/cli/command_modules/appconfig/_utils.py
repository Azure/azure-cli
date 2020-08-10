from __future__ import print_function

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from knack.prompting import NoTTYException, prompt_y_n
from knack.util import CLIError

from ._client_factory import cf_configstore


def construct_connection_string(cmd, config_store_name):
    connection_string_template = 'Endpoint={};Id={};Secret={}'

    try:
        resource_group_name, endpoint = resolve_resource_group(
            cmd, config_store_name)
        config_store_client = cf_configstore(cmd.cli_ctx)
        access_keys = config_store_client.list_keys(
            resource_group_name, config_store_name)
        for entry in access_keys:
            if not entry.read_only:
                return connection_string_template.format(endpoint, entry.id, entry.value)
    except Exception:
        raise CLIError(
            'Cannot find the App Configuration {}. Check if it exists in the subscription that logged in. '.format(config_store_name))

    raise CLIError('Cannot find a read write access key for the App Configuration {}'.format(
        config_store_name))


def resolve_resource_group(cmd, config_store_name):
    config_store_client = cf_configstore(cmd.cli_ctx)
    all_stores = config_store_client.list()
    for store in all_stores:
        if store.name.lower() == config_store_name.lower():
            # Id has a fixed structure /subscriptions/subscriptionName/resourceGroups/groupName/providers/providerName/configurationStores/storeName"
            return store.id.split('/')[4], store.endpoint
    raise CLIError(
        "App Configuration store: {} does not exist".format(config_store_name))


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
            'Please specify config store name or connection string(suggested).')
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
