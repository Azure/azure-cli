from __future__ import print_function

from azure.cli.commands import CommandTable
from azure.cli.commands._auto_command import build_operation, CommandDefinition

from ._params import PARAMETER_ALIASES
from .custom import ProfileCommands

command_table = CommandTable()

# PROFILE COMMANDS

build_operation(
    '', None, ProfileCommands,
    [
        CommandDefinition(ProfileCommands.login, 'Result'),
    ], command_table, PARAMETER_ALIASES)

build_operation(
    '', None, ProfileCommands,
    [
        CommandDefinition(ProfileCommands.logout, 'Result'),
    ], command_table, PARAMETER_ALIASES)

build_operation(
    'account', None, ProfileCommands,
    [
        CommandDefinition(ProfileCommands.list_subscriptions, '[Subscription]', 'list'),
        CommandDefinition(ProfileCommands.set_active_subscription, 'Result', 'set'),
        CommandDefinition(ProfileCommands.account_clear, 'Result', 'clear'),
    ], command_table, PARAMETER_ALIASES)
