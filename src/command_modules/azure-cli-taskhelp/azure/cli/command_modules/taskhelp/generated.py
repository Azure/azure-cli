#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function

from azure.cli.core.commands import cli_command

from .custom import deploy_arm_template

cli_command('taskhelp deploy-arm-template', deploy_arm_template)
