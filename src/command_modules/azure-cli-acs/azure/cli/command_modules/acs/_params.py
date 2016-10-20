#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliArgumentType, register_cli_argument
from azure.cli.core.commands.parameters import (
    name_type,
    resource_group_name_type, 
    get_resource_group_completion_list)

register_cli_argument('acs dcos browse', 'name', arg_type=name_type)
register_cli_argument('acs dcos browse', 'resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list)