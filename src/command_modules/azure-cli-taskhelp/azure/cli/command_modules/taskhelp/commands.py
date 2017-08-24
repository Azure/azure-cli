# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
    cli_command(__name__, 'taskhelp deploy-arm-template',
                'azure.cli.command_modules.taskhelp.custom#deploy_arm_template')
