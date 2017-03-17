# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

#pylint: disable=line-too-long

cli_command(__name__, 'project continuous-deployment create', 'azure.cli.command_modules.project.custom#create_continuous_deployment')
# TODO: Add help for this command
cli_command(__name__, 'project create', 'azure.cli.command_modules.project.custom#create_project')
cli_command(__name__, 'project browse jenkins', 'azure.cli.command_modules.project.custom#browse_jenkins')

#InnerLoop Commands
cli_command(__name__, 'project temp-command-setup', 'azure.cli.command_modules.project.custom#setup')
cli_command(__name__, 'project run', 'azure.cli.command_modules.project.custom#service_run')
