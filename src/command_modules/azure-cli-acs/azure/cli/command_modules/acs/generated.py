#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

from .custom import (
    dcos_browse)

from .custom import (
    dcos_install)

cli_command('acs dcos browse', dcos_browse)
cli_command('acs dcos install', dcos_install)