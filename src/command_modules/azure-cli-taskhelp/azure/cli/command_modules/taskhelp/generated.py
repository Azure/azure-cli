from __future__ import print_function

from azure.cli.commands import cli_command, command_table

from .custom import deploy_arm_template

cli_command(command_table, 'taskhelp deploy-arm-template', deploy_arm_template)
