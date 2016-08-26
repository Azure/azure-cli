#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function

from azure.cli.commands import cli_command

from .custom import (list_components, install, update, update_all, update_self, remove,
                     check_component)

# HELPER METHODS

cli_command('component list', list_components)
cli_command('component install', install)
cli_command('component update', update)
cli_command('component update-all', update_all)
cli_command('component update-self', update_self)
cli_command('component remove', remove)
cli_command('component check', check_component)
