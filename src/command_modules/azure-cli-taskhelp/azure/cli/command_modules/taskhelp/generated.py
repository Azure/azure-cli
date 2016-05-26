from __future__ import print_function

from azure.cli.commands import CommandTable
from azure.cli.commands.command_types import cli_command

from .custom import deploy_arm_template

command_table = CommandTable()

cli_command(command_table, 'taskhelp deploy-arm-template', deploy_arm_template, 'Help')
