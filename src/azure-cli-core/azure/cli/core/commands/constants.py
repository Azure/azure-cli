# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.parser import ARGPARSE_SUPPORTED_KWARGS


CLI_COMMON_KWARGS = ['min_api', 'max_api', 'resource_type', 'operation_group',
                     'custom_command_type', 'command_type']

CLI_COMMAND_KWARGS = ['transform', 'table_transformer', 'confirmation', 'exception_handler',
                      'client_factory', 'operations_tmpl', 'no_wait_param', 'supports_no_wait', 'validator',
                      'client_arg_name', 'doc_string_source', 'deprecate_info'] + CLI_COMMON_KWARGS
CLI_PARAM_KWARGS = \
    ['id_part', 'completer', 'validator', 'options_list', 'configured_default', 'arg_group', 'arg_type',
     'deprecate_info'] \
    + CLI_COMMON_KWARGS + ARGPARSE_SUPPORTED_KWARGS

CLI_POSITIONAL_PARAM_KWARGS = \
    ['completer', 'validator', 'configured_default', 'arg_type',
     'dest', 'default', 'type', 'help', 'metavar', 'action', 'nargs'] \
    + CLI_COMMAND_KWARGS  # specify which argparse kwargs are supported

CONFIRM_PARAM_NAME = 'yes'

# 1 hour in milliseconds
DEFAULT_QUERY_TIME_RANGE = 3600000

BLACKLISTED_MODS = ['context', 'shell', 'documentdb', 'component']
