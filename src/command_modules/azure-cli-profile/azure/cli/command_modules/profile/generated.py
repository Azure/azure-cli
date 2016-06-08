from __future__ import print_function

from azure.cli.commands import command_table, cli_command

from .custom import login, logout, list_subscriptions, set_active_subscription, account_clear

cli_command(command_table, 'login', login)
cli_command(command_table, 'logout', logout)

cli_command(command_table, 'account list', list_subscriptions)
cli_command(command_table, 'account set', set_active_subscription)
cli_command(command_table, 'account clear', account_clear)
