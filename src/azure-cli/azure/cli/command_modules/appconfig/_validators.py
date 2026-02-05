# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
import azure.cli.core.azclierror as CLIErrors

from datetime import datetime
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.azclierror import (InvalidArgumentValueError,
                                       RequiredArgumentMissingError,
                                       MutuallyExclusiveArgumentError,
                                       ArgumentUsageError)

from ._utils import (is_valid_connection_string,
                     resolve_store_metadata,
                     get_store_name_from_connection_string,
                     get_store_endpoint_from_connection_string,
                     validate_feature_flag_name,
                     validate_feature_flag_key,
                     is_http_endpoint)
from ._models import QueryFields
from ._constants import ImportExportProfiles
from ._featuremodels import FeatureQueryFields
from ._snapshotmodels import SnapshotQueryFields

logger = get_logger(__name__)


def validate_datetime(namespace):
    ''' valid datetime format: YYYY-MM-DDThh:mm:ss["Z"/±hh:mm]'''
    supported_formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%Sz", "%Y-%m-%dT%H:%M:%S%z"]
    if namespace.datetime is not None:
        for supported_format in supported_formats:
            if __tryparse_datetime(namespace.datetime, supported_format):
                return

        raise InvalidArgumentValueError('The input datetime is invalid. Correct format should be YYYY-MM-DDThh:mm:ss["Z"/±hh:mm].')


def __tryparse_datetime(datetime_string, dt_format):
    try:
        datetime.strptime(datetime_string, dt_format)
        return True
    except ValueError:
        return False


def validate_connection_string(cmd, namespace):
    ''' Endpoint=https://example.azconfig.io;Id=xxxxx;Secret=xxxx'''
    # Only use defaults when both name and connection string not specified
    if not (namespace.connection_string or namespace.name):
        namespace.connection_string = cmd.cli_ctx.config.get('defaults', 'appconfig_connection_string', None) or cmd.cli_ctx.config.get('appconfig', 'connection_string', None)
        namespace.name = cmd.cli_ctx.config.get('defaults', 'app_configuration_store', None)

    connection_string = namespace.connection_string
    if connection_string:
        if not is_valid_connection_string(connection_string):
            raise CLIError('''The connection string is invalid. \
Correct format should be Endpoint=https://example.azconfig.io;Id=xxxxx;Secret=xxxx ''')


def validate_auth_mode(namespace):
    auth_mode = namespace.auth_mode
    endpoint = getattr(namespace, 'endpoint', None)
    connection_string = getattr(namespace, 'connection_string', None)

    if auth_mode != "anonymous":
        # Disallow HTTP endpoints unless explicitly using anonymous mode.
        if endpoint and is_http_endpoint(endpoint):
            raise CLIError("HTTP endpoint is only supported when auth mode is 'anonymous'.")

        if connection_string:
            conn_endpoint = get_store_endpoint_from_connection_string(connection_string)
            if is_http_endpoint(conn_endpoint):
                raise CLIError("HTTP endpoint is only supported when auth mode is 'anonymous'.")

    if auth_mode == "login":
        if not namespace.name and not endpoint:
            raise CLIError("App Configuration name or endpoint should be provided if auth mode is 'login'.")
        if connection_string:
            raise CLIError("Auth mode should be 'key' when connection string is provided.")

    if auth_mode == "anonymous":
        if not endpoint:
            raise RequiredArgumentMissingError("App Configuration endpoint should be provided if auth mode is 'anonymous'.")
        if connection_string:
            raise CLIError("Auth mode 'anonymous' only supports the '--endpoint' argument. Connection string is not supported.")


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
    elif source == 'aks':
        if namespace.aks_cluster is None:
            raise RequiredArgumentMissingError("Please provide '--aks-cluster' argument")
        if namespace.configmap_name is None:
            raise RequiredArgumentMissingError("Please provide '--configmap-name' argument")


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
    from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
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


def validate_aks_cluster_name_or_id(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
    if namespace.aks_cluster:
        if not is_valid_resource_id(namespace.aks_cluster):
            config_store_name = ""
            if namespace.name:
                config_store_name = namespace.name
            elif namespace.connection_string:
                config_store_name = get_store_name_from_connection_string(namespace.connection_string)
            else:
                raise ArgumentUsageError("Please provide App Configuration name or connection string for fetching the AKS cluster details. Alternatively, you can provide a valid ARM ID for the AKS cluster.")

            resource_group, _ = resolve_store_metadata(cmd, config_store_name)
            namespace.aks_cluster = {
                "subscription": get_subscription_id(cmd.cli_ctx),
                "resource_group": resource_group,
                "name": namespace.aks_cluster
            }
        else:
            namespace.aks_cluster = parse_resource_id(namespace.aks_cluster)


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


def validate_snapshot_query_fields(namespace):
    if namespace.fields:
        fields = []
        for field in namespace.fields:
            for snapshot_query_field in SnapshotQueryFields:
                if field.lower() == snapshot_query_field.name.lower():
                    fields.append(snapshot_query_field)
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
        from azure.mgmt.core.tools import is_valid_resource_id
        if identity == '[all]' and subcommand == 'remove':
            continue

        if identity != '[system]' and not is_valid_resource_id(identity):
            raise InvalidArgumentValueError("Invalid identity '{}'. Use '[system]' to refer system assigned identity, or a resource id to refer user assigned identity.".format(identity))


def validate_secret_identifier(namespace):
    """ Validate the format of keyvault reference secret identifier """
    from azure.keyvault.secrets._shared import parse_key_vault_id

    identifier = getattr(namespace, 'secret_identifier', None)
    try:
        # this throws an exception for invalid format of secret identifier
        parse_key_vault_id(source_id=identifier)
    except Exception as e:
        raise CLIError("Received an exception while validating the format of secret identifier.\n{0}".format(str(e)))


def validate_key(namespace):
    if not namespace.key or str(namespace.key).isspace():
        raise RequiredArgumentMissingError("Key cannot be empty.")

    input_key = str(namespace.key).lower()
    if input_key == '.' or input_key == '..' or '%' in input_key:
        raise InvalidArgumentValueError("Key is invalid. Key cannot be a '.' or '..', or contain the '%' character.")


def validate_resolve_keyvault(namespace):
    if namespace.resolve_keyvault:
        identifier = getattr(namespace, 'destination', None)
        if identifier and identifier != "file":
            raise InvalidArgumentValueError("--resolve-keyvault is only applicable for exporting to file.")


def validate_feature(namespace):
    if namespace.feature is not None:
        validate_feature_flag_name(namespace.feature)


def validate_feature_key(namespace):
    if namespace.key is not None:
        validate_feature_flag_key(namespace.key)


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
        if namespace.tags:
            raise __construct_kvset_invalid_argument_error(is_exporting=False, argument='tags')


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
        if namespace.dest_tags:
            raise __construct_kvset_invalid_argument_error(is_exporting=True, argument='dest-tags')


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

        if namespace.snapshot:
            raise MutuallyExclusiveArgumentError("Cannot export snapshot key-values as references to App Service.")


def __construct_kvset_invalid_argument_error(is_exporting, argument):
    action = 'exporting' if is_exporting else 'importing'
    return InvalidArgumentValueError("The option '{0}' is not supported when {1} using '{2}' profile".format(argument, action, ImportExportProfiles.KVSET))


def validate_snapshot_filters(namespace):
    if not namespace.filters:
        raise RequiredArgumentMissingError("A list of at least one filter is required.")

    if isinstance(namespace.filters, list):
        if len(namespace.filters) < 1:
            raise InvalidArgumentValueError("At least one filter is required.")

        if len(namespace.filters) > 3:
            raise InvalidArgumentValueError("Too many filters supplied. A maximum of 3 filters allowed.")

        filter_parameters = []

        for filter_param in namespace.filters:
            try:
                parsed_filter = json.loads(filter_param)
                if not isinstance(parsed_filter, dict):
                    raise InvalidArgumentValueError('Parameter must be an escaped JSON object. Value of type {} was supplied.'.format(type(parsed_filter).__name__))

                key_filter_value = parsed_filter.get("key", None)

                if not key_filter_value:
                    raise InvalidArgumentValueError("Key filter value required.")

                if not isinstance(key_filter_value, str) or len(key_filter_value) < 1:
                    raise InvalidArgumentValueError("Invalid key filter value. Value must be a non-empty string.")

                if parsed_filter.get("label", None) and not isinstance(parsed_filter["label"], str):
                    raise InvalidArgumentValueError("Label filter must be a string if specified.")

                if parsed_filter.get("tags", None):
                    if not isinstance(parsed_filter["tags"], list) or not all(isinstance(tag, str) for tag in parsed_filter["tags"]):
                        raise InvalidArgumentValueError("Tags filter must be a list of strings if specified.")

                filter_parameters.append(parsed_filter)

            except ValueError:
                raise InvalidArgumentValueError("Parameter must be an escaped JSON object. {} is not a valid JSON object.".format(filter_param))

        namespace.filters = filter_parameters


def validate_snapshot_export(namespace):
    if namespace.snapshot:
        if any([namespace.key, namespace.label, namespace.skip_features, namespace.skip_keyvault]):
            raise MutuallyExclusiveArgumentError("'--snapshot' cannot be specified with '--key',  '--label', '--skip-keyvault' or '--skip-features' arguments.")


def validate_snapshot_import(namespace):
    if namespace.src_snapshot:
        if namespace.source != 'appconfig':
            raise InvalidArgumentValueError("--src-snapshot is only applicable when importing from a configuration store.")
        if any([namespace.src_key, namespace.src_label, namespace.skip_features]):
            raise MutuallyExclusiveArgumentError("'--src-snapshot' cannot be specified with '--src-key', '--src-label', or '--skip-features' arguments.")


def validate_sku(namespace):
    if namespace.sku.lower() == 'free':
        if (namespace.enable_purge_protection or namespace.retention_days or namespace.replica_name or namespace.replica_location or namespace.no_replica or namespace.enable_arm_private_network_access):  # pylint: disable=too-many-boolean-expressions
            logger.warning("Options '--enable-purge-protection', '--replica-name', '--replica-location' , '--no-replica' , 'enable-arm-private-network-access' and '--retention-days' will be ignored when creating a free store.")
            namespace.retention_days = None
            namespace.enable_purge_protection = None
            namespace.replica_name = None
            namespace.replica_location = None
            namespace.no_replica = None
            namespace.enable_arm_private_network_access = None
            return

    if namespace.sku.lower() == 'developer':
        if (namespace.enable_purge_protection or namespace.retention_days or namespace.replica_name or namespace.replica_location or namespace.no_replica):  # pylint: disable=too-many-boolean-expressions
            logger.warning("Options '--enable-purge-protection', '--replica-name', '--replica-location' , '--no-replica' and '--retention-days' will be ignored when creating a developer store.")
            namespace.retention_days = None
            namespace.enable_purge_protection = None
            namespace.replica_name = None
            namespace.replica_location = None
            namespace.no_replica = None
            return

    if namespace.sku.lower() == 'premium' and not namespace.no_replica:
        if any(arg is None for arg in [namespace.replica_name, namespace.replica_location]):
            raise RequiredArgumentMissingError("Options '--replica-name' and '--replica-location' are required when creating a premium tier store. To avoid creating replica please provide explicit argument '--no-replica'.")

    if namespace.no_replica and (namespace.replica_name or namespace.replica_location):
        raise CLIErrors.MutuallyExclusiveArgumentError("Please provide either '--no-replica' or both '--replica-name' and '--replica-location'. See 'az appconfig create -h' for examples.")

    if namespace.replica_name:
        if namespace.replica_location is None:
            raise RequiredArgumentMissingError("To create a replica, '--replica-location' is required.")
    else:
        if namespace.replica_location is not None:
            raise RequiredArgumentMissingError("To create a replica, '--replica-name' is required.")


def _validate_tag_filter_list(tag_list):
    if not tag_list or not isinstance(tag_list, list):
        return

    if len(tag_list) > 5:
        raise InvalidArgumentValueError("Too many tag filters provided. Maximum allowed is 5.")

    for tag in tag_list:
        if tag:
            comps = tag.split('=', 1)
            if comps[0] == "":
                raise InvalidArgumentValueError("Tag filter name cannot be empty.")


def validate_tag_filters(namespace):
    """Validates tag filters in the 'tags' attribute."""
    _validate_tag_filter_list(getattr(namespace, 'tags', None))


def validate_import_tag_filters(namespace):
    """Validates tag filters in the 'src_tags' attribute."""
    _validate_tag_filter_list(getattr(namespace, 'src_tags', None))


def validate_dry_run(namespace):
    if namespace.dry_run and namespace.yes:
        raise MutuallyExclusiveArgumentError("The '--dry-run' and '--yes' options cannot be specified together.")


def validate_kv_revision_retention_period(namespace):
    if namespace.kv_revision_retention_period is None:
        return

    retention_period = int(namespace.kv_revision_retention_period)

    if retention_period < 0:
        raise InvalidArgumentValueError("The key value revision retention period cannot be negative.")
