# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
import re
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.azclierror import (InvalidArgumentValueError,
                                       RequiredArgumentMissingError,
                                       MutuallyExclusiveArgumentError,
                                       ArgumentUsageError)

from ._utils import is_valid_connection_string, resolve_store_metadata, get_store_name_from_connection_string
from ._models import QueryFields
from ._constants import FeatureFlagConstants, ImportExportProfiles
from ._featuremodels import FeatureQueryFields

logger = get_logger(__name__)


def validate_datetime(namespace):
    ''' valid datetime format:YYYY-MM-DDThh:mm:ssZ '''
    datetime_format = '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])T(2[0-3]|[01][0-9]):[0-5][0-9]:[0-5][0-9][a-zA-Z]{0,5}$'
    if namespace.datetime is not None and re.search(datetime_format, namespace.datetime) is None:
        raise CLIError(
            'The input datetime is invalid. Correct format should be YYYY-MM-DDThh:mm:ssZ ')


def validate_connection_string(namespace):
    ''' Endpoint=https://example.azconfig.io;Id=xxxxx;Secret=xxxx'''
    connection_string = namespace.connection_string
    if connection_string:
        if not is_valid_connection_string(connection_string):
            raise CLIError('''The connection string is invalid. \
Correct format should be Endpoint=https://example.azconfig.io;Id=xxxxx;Secret=xxxx ''')


def validate_auth_mode(namespace):
    auth_mode = namespace.auth_mode
    if auth_mode == "login":
        if not namespace.name and not namespace.endpoint:
            raise CLIError("App Configuration name or endpoint should be provided if auth mode is 'login'.")
        if namespace.connection_string:
            raise CLIError("Auth mode should be 'key' when connection string is provided.")


def validate_import_depth(namespace):
    depth = namespace.depth
    if depth is not None:
        try:
            depth = int(depth)
            if depth < 1:
                raise InvalidArgumentValueError('Depth should be at least 1.')
        except ValueError:
            raise InvalidArgumentValueError("Depth is not a number.")


def validate_separator(namespace):
    if namespace.separator is not None:
        if namespace.format_ == "properties":
            raise ArgumentUsageError("Separator is not needed for properties file.")
        valid_separators = ['.', ',', ';', '-', '_', '__', '/', ':']
        if namespace.separator not in valid_separators:
            raise InvalidArgumentValueError(
                "Unsupported separator, allowed values: '.', ',', ';', '-', '_', '__', '/', ':'.")


def validate_import(namespace):
    source = namespace.source
    if source == 'file':
        if namespace.path is None:
            raise RequiredArgumentMissingError("Please provide the '--path' argument.")
        if namespace.format_ is None:
            raise RequiredArgumentMissingError("Please provide the '--format' argument.")
    elif source == 'appconfig':
        if (namespace.src_name is None) and (namespace.src_connection_string is None) and (namespace.src_endpoint is None):
            raise RequiredArgumentMissingError("Please provide '--src-name', '--src-connection-string' or '--src-endpoint' argument.")
    elif source == 'appservice':
        if namespace.appservice_account is None:
            raise RequiredArgumentMissingError("Please provide '--appservice-account' argument")


def validate_export(namespace):
    destination = namespace.destination
    if destination == 'file':
        if namespace.path is None:
            raise RequiredArgumentMissingError("Please provide the '--path' argument.")
        if namespace.format_ is None:
            raise RequiredArgumentMissingError("Please provide the '--format' argument.")
    elif destination == 'appconfig':
        if (namespace.dest_name is None) and (namespace.dest_connection_string is None) and (namespace.dest_endpoint is None):
            raise RequiredArgumentMissingError("Please provide '--dest-name', '--dest-connection-string' or '--dest-endpoint' argument.")
    elif destination == 'appservice':
        if namespace.appservice_account is None:
            raise RequiredArgumentMissingError("Please provide '--appservice-account' argument")


def validate_appservice_name_or_id(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, parse_resource_id
    if namespace.appservice_account:
        if not is_valid_resource_id(namespace.appservice_account):
            config_store_name = ""
            if namespace.name:
                config_store_name = namespace.name
            elif namespace.connection_string:
                config_store_name = get_store_name_from_connection_string(namespace.connection_string)
            else:
                raise CLIError("Please provide App Configuration name or connection string for fetching the AppService account details. Alternatively, you can provide a valid ARM ID for the Appservice account.")

            resource_group, _ = resolve_store_metadata(cmd, config_store_name)
            namespace.appservice_account = {
                "subscription": get_subscription_id(cmd.cli_ctx),
                "resource_group": resource_group,
                "name": namespace.appservice_account
            }
        else:
            namespace.appservice_account = parse_resource_id(namespace.appservice_account)


def validate_query_fields(namespace):
    if namespace.fields:
        fields = []
        for field in namespace.fields:
            for query_field in QueryFields:
                if field.lower() == query_field.name.lower():
                    fields.append(query_field)
        namespace.fields = fields


def validate_feature_query_fields(namespace):
    if namespace.fields:
        fields = []
        for field in namespace.fields:
            for feature_query_field in FeatureQueryFields:
                if field.lower() == feature_query_field.name.lower():
                    fields.append(feature_query_field)
        namespace.fields = fields


def validate_filter_parameters(namespace):
    """ Extracts multiple space-separated filter paramters in name[=value] format """
    if isinstance(namespace.filter_parameters, list):
        filter_parameters_dict = {}
        for item in namespace.filter_parameters:
            param_tuple = validate_filter_parameter(item)
            if param_tuple:
                # pylint: disable=unbalanced-tuple-unpacking
                param_name, param_value = param_tuple
                # If param_name already exists, error out
                if param_name in filter_parameters_dict:
                    raise CLIError('Filter parameter name "{}" cannot be duplicated.'.format(param_name))
                filter_parameters_dict.update({param_name: param_value})
        namespace.filter_parameters = filter_parameters_dict


def validate_filter_parameter(string):
    """ Extracts a single filter parameter in name[=value] format """
    result = ()
    if string:
        comps = string.split('=', 1)

        if comps[0]:
            if len(comps) > 1:
                # In the portal, if value textbox is blank we store the value as empty string.
                # In CLI, we should allow inputs like 'name=', which correspond to empty string value.
                # But there is no way to differentiate between CLI inputs 'name=' and 'name=""'.
                # So even though "" is invalid JSON escaped string, we will accept it and set the value as empty string.
                filter_param_value = '\"\"' if comps[1] == "" else comps[1]
                try:
                    # Ensure that provided value of this filter parameter is valid JSON. Error out if value is invalid JSON.
                    filter_param_value = json.loads(filter_param_value)
                except ValueError:
                    raise InvalidArgumentValueError('Filter parameter value must be a JSON escaped string. "{}" is not a valid JSON object.'.format(filter_param_value))
                result = (comps[0], filter_param_value)
            else:
                result = (string, '')
        else:
            # Error out on invalid arguments like '=value' or '='
            raise InvalidArgumentValueError('Invalid filter parameter "{}". Parameter name cannot be empty.'.format(string))
    return result


def validate_identity(namespace):
    subcommand = namespace.command.split(' ')[-1]
    identities = set()

    if subcommand == 'create' and namespace.assign_identity:
        identities = set(namespace.assign_identity)
    elif subcommand in ('assign', 'remove') and namespace.identities:
        identities = set(namespace.identities)
    else:
        return

    for identity in identities:
        from msrestazure.tools import is_valid_resource_id
        if identity == '[all]' and subcommand == 'remove':
            continue

        if identity != '[system]' and not is_valid_resource_id(identity):
            raise InvalidArgumentValueError("Invalid identity '{}'. Use '[system]' to refer system assigned identity, or a resource id to refer user assigned identity.".format(identity))


def validate_secret_identifier(namespace):
    """ Validate the format of keyvault reference secret identifier """
    from azure.keyvault.key_vault_id import KeyVaultIdentifier

    identifier = getattr(namespace, 'secret_identifier', None)
    try:
        # this throws an exception for invalid format of secret identifier
        KeyVaultIdentifier(uri=identifier)
    except Exception as e:
        raise CLIError("Received an exception while validating the format of secret identifier.\n{0}".format(str(e)))


def validate_key(namespace):
    if namespace.key:
        input_key = str(namespace.key).lower()
        if input_key == '.' or input_key == '..' or '%' in input_key:
            raise InvalidArgumentValueError("Key is invalid. Key cannot be a '.' or '..', or contain the '%' character.")
    else:
        raise RequiredArgumentMissingError("Key cannot be empty.")


def validate_resolve_keyvault(namespace):
    if namespace.resolve_keyvault:
        identifier = getattr(namespace, 'destination', None)
        if identifier and identifier != "file":
            raise InvalidArgumentValueError("--resolve-keyvault is only applicable for exporting to file.")


def validate_feature(namespace):
    if namespace.feature is not None:
        if '%' in namespace.feature:
            raise InvalidArgumentValueError("Feature name cannot contain the '%' character.")
        if not namespace.feature:
            raise InvalidArgumentValueError("Feature name cannot be empty.")


def validate_feature_key(namespace):
    if namespace.key is not None:
        input_key = str(namespace.key).lower()
        if '%' in input_key:
            raise InvalidArgumentValueError("Feature flag key cannot contain the '%' character.")
        if not input_key.startswith(FeatureFlagConstants.FEATURE_FLAG_PREFIX):
            raise InvalidArgumentValueError("Feature flag key must start with the reserved prefix '{0}'.".format(FeatureFlagConstants.FEATURE_FLAG_PREFIX))
        if len(input_key) == len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):
            raise InvalidArgumentValueError("Feature flag key must contain more characters after the reserved prefix '{0}'.".format(FeatureFlagConstants.FEATURE_FLAG_PREFIX))


def validate_import_profile(namespace):
    if namespace.profile == ImportExportProfiles.KVSET:
        if namespace.source != 'file':
            raise InvalidArgumentValueError("Import profile '{}' can only be used when importing from a JSON file.".format(ImportExportProfiles.KVSET))
        if namespace.format_ != 'json':
            raise InvalidArgumentValueError("Import profile '{}' can only be used when importing from a JSON format.".format(ImportExportProfiles.KVSET))
        if namespace.content_type is not None:
            raise __construct_kvset_invalid_argument_error(is_exporting=False, argument='content-type')
        if namespace.label is not None:
            raise __construct_kvset_invalid_argument_error(is_exporting=False, argument='label')
        if namespace.separator is not None:
            raise __construct_kvset_invalid_argument_error(is_exporting=False, argument='separator')
        if namespace.depth is not None:
            raise __construct_kvset_invalid_argument_error(is_exporting=False, argument='depth')
        if namespace.prefix is not None and namespace.prefix != '':
            raise __construct_kvset_invalid_argument_error(is_exporting=False, argument='prefix')
        if namespace.skip_features:
            raise __construct_kvset_invalid_argument_error(is_exporting=False, argument='skip-features')


def validate_export_profile(namespace):
    if namespace.profile == ImportExportProfiles.KVSET:
        if namespace.destination != 'file':
            raise InvalidArgumentValueError("The profile '{}' only supports exporting to a file.".format(ImportExportProfiles.KVSET))
        if namespace.format_ != 'json':
            raise InvalidArgumentValueError("The profile '{}' only supports exporting in the JSON format".format(ImportExportProfiles.KVSET))
        if namespace.prefix is not None and namespace.prefix != '':
            raise __construct_kvset_invalid_argument_error(is_exporting=True, argument='prefix')
        if namespace.dest_label is not None:
            raise __construct_kvset_invalid_argument_error(is_exporting=True, argument='dest-label')
        if namespace.resolve_keyvault:
            raise __construct_kvset_invalid_argument_error(is_exporting=True, argument='resolve-keyvault')
        if namespace.separator is not None:
            raise __construct_kvset_invalid_argument_error(is_exporting=True, argument='separator')


def validate_strict_import(namespace):
    if namespace.strict:
        if namespace.skip_features:
            raise MutuallyExclusiveArgumentError("The option '--skip-features' cannot be used with the '--strict' option.")
        if namespace.source != 'file':
            raise InvalidArgumentValueError("The option '--strict' can only be used when importing from a file.")


def validate_export_as_reference(namespace):
    if namespace.export_as_reference:
        if namespace.destination != 'appservice':
            raise InvalidArgumentValueError("The option '--export-as-reference' can only be used when exporting to app service.")


def __construct_kvset_invalid_argument_error(is_exporting, argument):
    action = 'exporting' if is_exporting else 'importing'
    return InvalidArgumentValueError("The option '{0}' is not supported when {1} using '{2}' profile".format(argument, action, ImportExportProfiles.KVSET))
