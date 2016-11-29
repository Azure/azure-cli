# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command

cli_command(__name__, 'component list', 'azure.cli.command_modules.component.custom#list_components')
cli_command(__name__, 'component update', 'azure.cli.command_modules.component.custom#update')
cli_command(__name__, 'component remove', 'azure.cli.command_modules.component.custom#remove')
cli_command(__name__, 'component list-available', 'azure.cli.command_modules.component.custom#list_available_components')
