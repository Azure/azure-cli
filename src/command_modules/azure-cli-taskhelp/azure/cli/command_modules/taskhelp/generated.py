from __future__ import print_function

from azure.cli.commands import cli_command

from .custom import deploy_arm_template

cli_command('taskhelp deploy-arm-template', deploy_arm_template)
