from __future__ import print_function

from azure.cli.commands import command_table, cli_command

from .custom import (list_components, install, update, update_all, update_self, remove,
                     check_component)

# HELPER METHODS

cli_command(command_table, 'component list', list_components)
cli_command(command_table, 'component install', install)
cli_command(command_table, 'component update', update)
cli_command(command_table, 'component update-all', update_all)
cli_command(command_table, 'component update-self', update_self)
cli_command(command_table, 'component remove', remove)
cli_command(command_table, 'component check', check_component)
