# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

# pylint: disable=line-too-long

cli_command(__name__, 'project deployment-pipeline browse',
            'azure.cli.command_modules.project.custom#browse_pipeline')
cli_command(__name__, 'project deployment-pipeline create',
            'azure.cli.command_modules.project.custom#create_deployment_pipeline')
cli_command(__name__, 'project reference add',
            'azure.cli.command_modules.project.custom#add_reference')

# TODO: Add help for this command
cli_command(__name__, 'project create',
            'azure.cli.command_modules.project.custom#create_project')
            
# InnerLoop Commands
cli_command(__name__, 'project run',
            'azure.cli.command_modules.project.custom#service_run')
cli_command(__name__, 'project service list', 
            'azure.cli.command_modules.project.custom#service_list')