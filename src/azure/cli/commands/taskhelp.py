from ..commands import command, description
from .._locale import L

@command('taskhelp deploy-arm-template')
@description(L('How to deploy and ARM template using Azure CLI.'))
def deploy_template_help(args, unexpected): #pylint: disable=unused-argument
    indent = 1
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
