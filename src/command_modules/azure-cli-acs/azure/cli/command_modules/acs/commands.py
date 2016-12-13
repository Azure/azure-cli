# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command

cli_command(__name__, 'acs browse', 'azure.cli.command_modules.acs.custom#acs_browse')
cli_command(__name__, 'acs install-cli', 'azure.cli.command_modules.acs.custom#acs_install_cli')
cli_command(__name__, 'acs dcos browse', 'azure.cli.command_modules.acs.custom#dcos_browse')
cli_command(__name__, 'acs dcos install-cli', 'azure.cli.command_modules.acs.custom#dcos_install_cli')
cli_command(__name__, 'acs create', 'azure.cli.command_modules.acs.custom#acs_create')
cli_command(__name__, 'acs kubernetes browse', 'azure.cli.command_modules.acs.custom#k8s_browse')
cli_command(__name__, 'acs kubernetes install-cli', 'azure.cli.command_modules.acs.custom#k8s_install_cli')
cli_command(__name__, 'acs kubernetes get-credentials', 'azure.cli.command_modules.acs.custom#k8s_get_credentials')

