# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

cli_command(__name__, 'cloud list', 'azure.cli.command_modules.cloud.custom#list_clouds')
cli_command(__name__, 'cloud show', 'azure.cli.command_modules.cloud.custom#show_cloud')
cli_command(__name__, 'cloud register', 'azure.cli.command_modules.cloud.custom#register_cloud')
cli_command(__name__, 'cloud unregister', 'azure.cli.command_modules.cloud.custom#unregister_cloud')
cli_command(__name__, 'cloud set', 'azure.cli.command_modules.cloud.custom#set_cloud')
cli_command(__name__, 'cloud update', 'azure.cli.command_modules.cloud.custom#modify_cloud')
cli_command(__name__, 'cloud list-profiles', 'azure.cli.command_modules.cloud.custom#list_profiles')
