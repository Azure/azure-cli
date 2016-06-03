from __future__ import print_function

from azure.cli.commands import CommandTable
from azure.cli.commands.command_types import cli_command

from .custom import login, logout, list_subscriptions, set_active_subscription, account_clear

command_table = CommandTable()

cli_command(command_table, 'login', login, 'Result')
cli_command(command_table, 'logout', logout, 'Result')

cli_command(command_table, 'account list', list_subscriptions)
cli_command(command_table, 'account set', set_active_subscription)
cli_command(command_table, 'account clear', account_clear)
