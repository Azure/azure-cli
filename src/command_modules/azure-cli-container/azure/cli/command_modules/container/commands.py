# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

#pylint: disable=line-too-long

cli_command(__name__, 'container release create', 'azure.cli.command_modules.container.custom#add_release')
cli_command(__name__, 'container release list', 'azure.cli.command_modules.container.custom#list_releases')

cli_command(__name__, 'container build create', 'azure.cli.command_modules.container.custom#add_ci')
