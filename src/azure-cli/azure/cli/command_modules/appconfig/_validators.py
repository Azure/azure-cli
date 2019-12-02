# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import re
from knack.log import get_logger
from knack.util import CLIError

from ._utils import is_valid_connection_string, resolve_resource_group
from ._azconfig.models import QueryFields
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


def validate_import_depth(namespace):
    depth = namespace.depth
    if depth is not None:
        try:
            depth = int(depth)
            if depth < 1:
                raise CLIError('Depth should be at least 1.')
        except ValueError:
            raise CLIError("Depth is not a number.")


def validate_separator(namespace):
    if namespace.separator is not None:
        if namespace.format_ == "properties":
            raise CLIError("Separator is not needed for properties file.")
        valid_separators = ['.', ',', ';', '-', '_', '__', '/', ':']
        if namespace.separator not in valid_separators:
            raise CLIError(
                "Unsupported separator, allowed values: '.', ',', ';', '-', '_', '__', '/', ':'.")


def validate_import(namespace):
    source = namespace.source
    if source == 'file':
        if namespace.path is None or namespace.format_ is None:
            raise CLIError("usage error: --path PATH --format FORMAT")
    elif source == 'appconfig':
        if (namespace.src_name is None) and (namespace.src_connection_string is None):
            raise CLIError("usage error: --config-name NAME | --connection-string STR")
    elif source == 'appservice':
        if namespace.appservice_account is None:
            raise CLIError("usage error: --appservice-account NAME_OR_ID")


def validate_export(namespace):
    destination = namespace.destination
    if destination == 'file':
        if namespace.path is None or namespace.format_ is None:
            raise CLIError("usage error: --path PATH --format FORMAT")
    elif destination == 'appconfig':
        if (namespace.dest_name is None) and (namespace.dest_connection_string is None):
            raise CLIError("usage error: --config-name NAME | --connection-string STR")
    elif destination == 'appservice':
        if namespace.appservice_name is None:
            raise CLIError("usage error: --appservice-account NAME_OR_ID")


def validate_appservice_name_or_id(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, parse_resource_id
    if namespace.appservice_account:
        if not is_valid_resource_id(namespace.appservice_account):
            resource_group, _ = resolve_resource_group(cmd, namespace.name)
            namespace.appservice_account = {
                "subscription": get_subscription_id(cmd.cli_ctx),
                "resource_group": resource_group,
                "name": namespace.appservice_account
            }
        else:
            namespace.appservice_account = parse_resource_id(
                namespace.appservice_account)


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
                param_name, param_value = param_tuple
                # If param_name already exists, convert the values to a list
                if param_name in filter_parameters_dict:
                    old_param_value = filter_parameters_dict[param_name]
                    if isinstance(old_param_value, list):
                        old_param_value.append(param_value)
                    else:
                        filter_parameters_dict[param_name] = [old_param_value, param_value]
                else:
                    filter_parameters_dict.update({param_name: param_value})
        namespace.filter_parameters = filter_parameters_dict


def validate_filter_parameter(string):
    """ Extracts a single filter parameter in name[=value] format """
    result = ()
    if string:
        comps = string.split('=', 1)
        # Ignore invalid arguments like  '=value' or '='
        if comps[0]:
            result = (comps[0], comps[1]) if len(comps) > 1 else (string, '')
        else:
            logger.warning("Ignoring filter parameter '%s' because parameter name is empty.", string)
    return result
