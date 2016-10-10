#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command_with_handler

from azure.cli.command_modules.component._operation_factory import *

cli_command_with_handler(__name__, 'component list', of_component_list)
cli_command_with_handler(__name__, 'component update', of_component_update)
cli_command_with_handler(__name__, 'component remove', of_component_remove)
