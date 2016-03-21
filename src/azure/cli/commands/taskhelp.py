from ..commands import command, description
from .._locale import L
from .._help import _print_indent

@command('taskhelp deploy_arm_template')
@description(L('How to deploy and ARM template using Azure CLI.'))
def logout(args, unexpected): #pylint: disable=unused-argument
    indent = 1
    _print_indent(L('''
***********************
ARM Template Deployment
***********************

Could this be helpful?  Let us know!
====================================

1. First Step
2. Second Step

And you're done!
'''), indent)
