#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command, DeploymentOutputLongRunningOperation

from .custom import (
    dcos_browse)

cli_command('acs dcos browse', dcos_browse)