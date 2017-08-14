# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command

_CONFIRM_MSG = "Extensions can modify existing commands as well as add new commands.\nOnly install extensions from trusted sources.\nAre you sure you want to add this extension?"

cli_command(__name__, 'extension add', 'azure.cli.command_modules.extension.custom#add_extension', confirmation=_CONFIRM_MSG)
cli_command(__name__, 'extension remove', 'azure.cli.command_modules.extension.custom#remove_extension', confirmation=True)
cli_command(__name__, 'extension list', 'azure.cli.command_modules.extension.custom#list_extensions')
cli_command(__name__, 'extension show', 'azure.cli.command_modules.extension.custom#show_extension')
