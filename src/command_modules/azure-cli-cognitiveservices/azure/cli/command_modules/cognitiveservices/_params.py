# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands import register_cli_argument, CliArgumentType

from azure.cli.core.commands.parameters import (
    tags_type,
    resource_group_name_type,
    get_resource_name_completion_list)

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')

register_cli_argument('cognitiveservices', 'account_name',
                      arg_type=name_arg_type, help='cognitive service account name',
                      completer=get_resource_name_completion_list(
                          'Microsoft.CognitiveServices/accounts'))
register_cli_argument('cognitiveservices', 'resource_group_name',
                      arg_type=resource_group_name_type)
register_cli_argument('cognitiveservices', 'sku_name', options_list=('--sku',),
                      help='the Sku of cognitive services account')
register_cli_argument('cognitiveservices', 'kind',
                      help='the API name of cognitive services account')
register_cli_argument('cognitiveservices', 'tags', tags_type)
register_cli_argument('cognitiveservices', 'key_name', required=True,
                      help='Key name to generate', choices=['key1', 'key2'])
register_cli_argument('cognitiveservices account create', 'yes', action='store_true',
                      help='Do not prompt for terms confirmation')
