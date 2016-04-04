from __future__ import print_function
from azure.cli.commands import CommandTable
from azure.cli._locale import L

command_table = CommandTable()

@command_table.command('taskhelp deploy-arm-template')
@command_table.description(L('How to deploy and ARM template using Azure CLI.'))
def deploy_template_help(args, unexpected): #pylint: disable=unused-argument
    print(L("""
***********************
ARM Template Deployment
***********************

Could this be helpful?  Let us know!
====================================

1. First Step
2. Second Step

And you're done!
"""))
