from __future__ import print_function

from azure.cli.commands import CommandTable
from azure.cli.commands._auto_command import build_operation, CommandDefinition

from ._params import PARAMETER_ALIASES
from .custom import ComponentCommands

command_table = CommandTable()

# HELPER METHODS

def _patch_aliases(alias_items):
    aliases = PARAMETER_ALIASES.copy()
    aliases.update(alias_items)
    return aliases

build_operation(
    'component', None, ComponentCommands,
    [
        CommandDefinition(ComponentCommands.list, '[Component]'),
        CommandDefinition(ComponentCommands.install, 'Result'),
        CommandDefinition(ComponentCommands.update, 'Result'),
        CommandDefinition(ComponentCommands.update_all, 'Result'),
        CommandDefinition(ComponentCommands.update_self, 'Result'),
        CommandDefinition(ComponentCommands.remove, 'Result'),
        CommandDefinition(ComponentCommands.check_component, 'Result', 'check')
    ], command_table, PARAMETER_ALIASES)
