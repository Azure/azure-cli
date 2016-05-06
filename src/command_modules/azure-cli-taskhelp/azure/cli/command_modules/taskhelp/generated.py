from __future__ import print_function

from azure.cli.commands import CommandTable
from azure.cli.commands._auto_command import build_operation, CommandDefinition

from .custom import TaskHelpCommands

command_table = CommandTable()

build_operation(
    'taskhelp', None, TaskHelpCommands,
    [
        CommandDefinition(TaskHelpCommands.deploy_arm_template, 'Help'),
    ], command_table)
