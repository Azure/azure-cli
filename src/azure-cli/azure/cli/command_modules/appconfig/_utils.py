# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from knack.log import get_logger
from knack.util import CLIError
from azure.appconfiguration import AzureAppConfigurationClient
from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import ValidationError, AzureResponseError, ResourceNotFoundError

from ._client_factory import cf_configstore
from ._constants import HttpHeaders

logger = get_logger(__name__)


def construct_connection_string(cmd, config_store_name):
    connection_string_template = 'Endpoint={};Id={};Secret={}'
    # If the logged in user/Service Principal does not have 'Reader' or 'Contributor' role
    # assigned for the requested AppConfig, resolve_store_metadata will raise CLI error
    resource_group_name, endpoint = resolve_store_metadata(cmd, config_store_name)

    try:
        config_store_client = cf_configstore(cmd.cli_ctx)
        access_keys = config_store_client.list_keys(resource_group_name, config_store_name)
        for entry in access_keys:
            if not entry.read_only:
                return connection_string_template.format(endpoint, entry.id, entry.value)
    except HttpResponseError as ex:
        raise CLIError('Failed to get access keys for the App Configuration "{}". Make sure that the account that logged in has sufficient permissions to access the App Configuration store.\n{}'.format(config_store_name, str(ex)))

    raise CLIError('Cannot find a read write access key for the App Configuration {}'.format(config_store_name))


def resolve_store_metadata(cmd, config_store_name):
    resource_group = None
    endpoint = None
    try:
        config_store_client = cf_configstore(cmd.cli_ctx)
        all_stores = config_store_client.list()
        for store in all_stores:
            if store.name.lower() == config_store_name.lower():
                if resource_group is None:
                    # Id has a fixed structure /subscriptions/subscriptionName/resourceGroups/groupName/providers/providerName/configurationStores/storeName"
                    resource_group = store.id.split('/')[4]
                    endpoint = store.endpoint
                else:
                    raise ValidationError('Multiple configuration stores found with name {}.'.format(config_store_name))
    except HttpResponseError as ex:
        raise AzureResponseError("Failed to get the list of App Configuration stores for the current user. Make sure that the account that logged in has sufficient permissions to access the App Configuration store.\n{}".format(str(ex)))

    if resource_group is not None and endpoint is not None:
        return resource_group, endpoint

    raise ResourceNotFoundError("Failed to find the App Configuration store '{}'.".format(config_store_name))


def resolve_deleted_store_metadata(cmd, config_store_name, resource_group_name, location):
    resource_group = None
    metadata_location = None
    try:
        client = cf_configstore(cmd.cli_ctx)
        deleted_stores = client.list_deleted()
        for deleted_store in deleted_stores:
            # configuration_store_id has a fixed structure /subscriptions/subscription_id/resourceGroups/resource_group_name/providers/Microsoft.AppConfiguration/configurationStores/configuration_store_name
            metadata_resource_group = deleted_store.configuration_store_id.split('/')[4]
            # match the name and additionally match resource group and location if available.
            if deleted_store.name.lower() == config_store_name.lower() and (resource_group_name is None or resource_group_name.lower() == metadata_resource_group.lower()) and (location is None or location == deleted_store.location):
                if metadata_location is None:
                    resource_group = metadata_resource_group
                    metadata_location = deleted_store.location
                else:
                    # It should reach here only when the user has provided only name. If they provide either location or resource group, we should be able to uniquely find the store.
                    raise ValidationError('Multiple configuration stores found with name {}.'.format(config_store_name))
    except HttpResponseError as ex:
        raise AzureResponseError("Failed to get the list of deleted App Configuration stores for the current user. Make sure that the account that logged in has sufficient permissions to access the App Configuration store.\n{}".format(str(ex)))

    if resource_group is not None and metadata_location is not None:
        return resource_group, metadata_location

    raise ResourceNotFoundError("Failed to find the deleted App Configuration store '{}'.".format(config_store_name))


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


def prep_label_filter_for_url_encoding(label=None):
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
        try:
            azconfig_client = AzureAppConfigurationClient.from_connection_string(connection_string=connection_string,
                                                                                 user_agent=HttpHeaders.USER_AGENT)
        except ValueError as ex:
            raise CLIError("Failed to initialize AzureAppConfigurationClient due to an exception: {}".format(str(ex)))

    if auth_mode == "login":
        if not endpoint:
            try:
                if name:
                    _, endpoint = resolve_store_metadata(cmd, name)
                else:
                    raise CLIError("App Configuration endpoint or name should be provided if auth mode is 'login'.")
            except Exception as ex:
                raise CLIError(str(ex) + "\nYou may be able to resolve this issue by providing App Configuration endpoint instead of name.")

        from azure.cli.core._profile import Profile
        profile = Profile(cli_ctx=cmd.cli_ctx)
        cred, _, _ = profile.get_login_credentials()
        try:
            azconfig_client = AzureAppConfigurationClient(credential=cred,
                                                          base_url=endpoint,
                                                          user_agent=HttpHeaders.USER_AGENT)
        except (ValueError, TypeError) as ex:
            raise CLIError("Failed to initialize AzureAppConfigurationClient due to an exception: {}".format(str(ex)))

    return azconfig_client
