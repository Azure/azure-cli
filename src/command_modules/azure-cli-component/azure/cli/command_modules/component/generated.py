#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

from .custom import (list_components, update, remove)

cli_command('component list', list_components)
cli_command('component update', update)
cli_command('component remove', remove)
