#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command, DeploymentOutputLongRunningOperation

from .custom import (
    add_release,
    list_releases,
    add_ci)

cli_command('devops release create', add_release)
cli_command('devops release list', list_releases)

cli_command('devops build create', add_ci)
