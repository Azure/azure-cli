# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from knack.log import get_logger
from knack.util import CLIError
from azure.appconfiguration import AzureAppConfigurationClient
from azure.core.exceptions import HttpResponseError
from azure.core.credentials import AzureKeyCredential
from azure.cli.core.azclierror import (ValidationError,
                                       AzureResponseError,
                                       InvalidArgumentValueError,
                                       ResourceNotFoundError,
                                       RequiredArgumentMissingError,
                                       MutuallyExclusiveArgumentError)
from azure.core.pipeline.transport import RequestsTransport  # pylint: disable=no-name-in-module
from ._client_factory import cf_configstore
from ._constants import HttpHeaders, FeatureFlagConstants

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


def resolve_deleted_store_metadata(cmd, config_store_name, resource_group_name=None, location=None):
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

    raise ResourceNotFoundError("Failed to find the deleted App Configuration store '{}'. If you think that the store name is correct, please validate all your input parameters again.".format(config_store_name))


def resolve_connection_string(cmd, config_store_name=None, connection_string=None):
    error_message = '''You may have specified both store name and connection string, which is a conflict.
Please specify exactly ONE (suggest connection string) in one of the following options:\n
1 pass in App Configuration store name as a parameter\n
2 pass in connection string as a parameter\n
3 preset App Configuration store name using 'az configure --defaults app_configuration_store=xxxx'\n
4 preset connection string using 'az configure --defaults appconfig_connection_string=xxxx'\n
5 preset connection in environment variable like set AZURE_APPCONFIG_CONNECTION_STRING=xxxx'''

    connection_string_from_args = ''

    if config_store_name:
        connection_string_from_args = construct_connection_string(cmd, config_store_name)

    if connection_string:
        if not is_valid_connection_string(connection_string):
            raise ValidationError(
                "The connection string argument is invalid. Correct format should be Endpoint=https://example.appconfig.io;Id=xxxxx;Secret=xxxx")

        # If both connection string specified and name specified, ensure that both arguments reference the same store
        if connection_string_from_args:
            if ';'.join(sorted(connection_string.split(';'))) != connection_string_from_args:
                raise MutuallyExclusiveArgumentError(error_message)
        else:
            connection_string_from_args = connection_string

    if connection_string_from_args:
        return connection_string_from_args

    raise RequiredArgumentMissingError(
        'Please specify config store name or connection string(suggested).')


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
    endpoint = get_store_endpoint_from_connection_string(connection_string)
    if endpoint:
        return endpoint.split("//")[1].split('.')[0]
    return None


def get_store_endpoint_from_connection_string(connection_string):
    if is_valid_connection_string(connection_string):
        segments = dict(seg.split("=", 1) for seg in connection_string.split(";"))
        return segments.get("Endpoint")
    return None


def prep_filter_for_url_encoding(filter_value=None):
    if filter_value is not None:
        import ast
        # ast library requires quotes around string
        filter_value = '"{0}"'.format(filter_value)
        filter_value = ast.literal_eval(filter_value)
    return filter_value


class AuthHeaderRequestsTransport(RequestsTransport):  # pylint: disable=too-few-public-methods
    def send(self, request, **kwargs):  # pylint: disable=arguments-differ
        # Strip any auth/signature headers to allow anonymous access
        if 'Authorization' in request.headers:
            del request.headers['Authorization']

        # Also remove HMAC signature header if present
        if 'x-ms-content-sha256' in request.headers:
            del request.headers['x-ms-content-sha256']

        return super().send(request, **kwargs)


def get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint):
    azconfig_client = None

    if auth_mode == "anonymous":
        try:
            azconfig_client = AzureAppConfigurationClient(
                base_url=endpoint,
                credential=AzureKeyCredential(key=""),
                id_credential="",
                user_agent=HttpHeaders.USER_AGENT,
                transport=AuthHeaderRequestsTransport())
        except (ValueError, TypeError) as ex:
            raise CLIError("Failed to initialize AzureAppConfigurationClient due to an exception: {}".format(str(ex)))

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
                    raise RequiredArgumentMissingError("App Configuration endpoint or name should be provided if auth mode is 'login'.")
            except Exception as ex:
                raise CLIError(str(ex) + "\nYou may be able to resolve this issue by providing App Configuration endpoint instead of name.")

        from azure.cli.core._profile import Profile
        from azure.cli.core.cloud import get_active_cloud
        from ._credential import AppConfigurationCliCredential
        profile = Profile(cli_ctx=cmd.cli_ctx)
        cred, _, _ = profile.get_login_credentials()

        current_cloud = get_active_cloud(cmd.cli_ctx)
        token_audience = None
        if hasattr(current_cloud.endpoints, "appconfig_auth_token_audience"):
            token_audience = current_cloud.endpoints.appconfig_auth_token_audience

        try:
            azconfig_client = AzureAppConfigurationClient(credential=AppConfigurationCliCredential(cred, token_audience),
                                                          base_url=endpoint,
                                                          user_agent=HttpHeaders.USER_AGENT)
        except (ValueError, TypeError) as ex:
            raise CLIError("Failed to initialize AzureAppConfigurationClient due to an exception: {}".format(str(ex)))

    return azconfig_client


def is_json_content_type(content_type):
    if not content_type:
        return False

    content_type = content_type.strip().lower()
    mime_type = content_type.split(';')[0].strip()

    type_parts = mime_type.split('/')
    if len(type_parts) != 2:
        return False

    (main_type, sub_type) = type_parts
    if main_type != "application":
        return False

    sub_types = sub_type.split('+')
    if "json" in sub_types:
        return True

    return False


def validate_feature_flag_name(feature):
    if feature:
        INVALID_FEATURE_CHARACTERS = ("%", ":")
        if any(invalid_char in feature for invalid_char in INVALID_FEATURE_CHARACTERS):
            raise InvalidArgumentValueError(
                "Feature name cannot contain the following characters: '{}'.".format("', '".join(INVALID_FEATURE_CHARACTERS)))

    else:
        raise InvalidArgumentValueError("Feature name cannot be empty.")


def validate_feature_flag_key(key):
    input_key = str(key).lower()
    if '%' in input_key:
        raise InvalidArgumentValueError("Feature flag key cannot contain the '%' character.")
    if not input_key.startswith(FeatureFlagConstants.FEATURE_FLAG_PREFIX):
        raise InvalidArgumentValueError("Feature flag key must start with the reserved prefix '{0}'.".format(FeatureFlagConstants.FEATURE_FLAG_PREFIX))
    if len(input_key) == len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):
        raise InvalidArgumentValueError("Feature flag key must contain more characters after the reserved prefix '{0}'.".format(FeatureFlagConstants.FEATURE_FLAG_PREFIX))


# Converts a list of tags in the format key[=value] into a dictionary.
# Ensures tags are properly parsed and formatted before adding to a key-value pair.
def parse_tags_to_dict(tags):
    """Converts a list of tags in key[=value] format to a dictionary."""
    if isinstance(tags, list):
        tags_dict = {}
        for item in tags:
            if item:
                comps = item.split('=', 1)
                tag_key = comps[0]
                tag_value = comps[1] if len(comps) > 1 else ''
                tags_dict[tag_key] = tag_value
        return tags_dict
    return tags


def is_http_endpoint(endpoint):
    if not endpoint:
        return False

    return str(endpoint).lower().startswith('http://')
