# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command

cli_command(__name__, 'login', 'azure.cli.command_modules.profile.custom#login')
cli_command(__name__, 'logout', 'azure.cli.command_modules.profile.custom#logout')

cli_command(__name__, 'account list', 'azure.cli.command_modules.profile.custom#list_subscriptions')
cli_command(__name__, 'account set', 'azure.cli.command_modules.profile.custom#set_active_subscription')
cli_command(__name__, 'account show', 'azure.cli.command_modules.profile.custom#show_subscription')
cli_command(__name__, 'account clear', 'azure.cli.command_modules.profile.custom#account_clear')
cli_command(__name__, 'account list-locations', 'azure.cli.command_modules.profile.custom#list_locations')
