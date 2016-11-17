# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

cli_command(__name__, 'context list', 'azure.cli.command_modules.context.custom#list_contexts')
cli_command(__name__, 'context show', 'azure.cli.command_modules.context.custom#show_contexts')
cli_command(__name__, 'context delete', 'azure.cli.command_modules.context.custom#delete_context')
cli_command(__name__, 'context create', 'azure.cli.command_modules.context.custom#create_context')
cli_command(__name__, 'context switch', 'azure.cli.command_modules.context.custom#activate_context')
cli_command(__name__, 'context modify', 'azure.cli.command_modules.context.custom#modify_context')
