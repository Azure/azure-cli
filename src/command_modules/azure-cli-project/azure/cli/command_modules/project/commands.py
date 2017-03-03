# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

#pylint: disable=line-too-long
cli_command(__name__, 'project continuous-deployment create', 'azure.cli.command_modules.project.custom#create_continuous_deployment')