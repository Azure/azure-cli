from __future__ import print_function
from azure.cli.commands import CommandTable
from azure.cli._locale import L

command_table = CommandTable()

@command_table.command('taskhelp deploy-arm-template')
@command_table.description(L('How to deploy and ARM template using Azure CLI.'))
def deploy_template_help(args): #pylint: disable=unused-argument
    print(L("""
[This is sample content]
Use the instructions in these sections to deploy a new Azure VM by using a template with the Azure CLI. This template creates a single virtual machine in a new virtual network with a single subnet, and unlike "azure vm quick-create", enables you to describe what you want precisely and repeat it without errors.

Templates are flexible, so the designer may have chosen to give you lots of parameters or chosen to offer only a few by creating a template that is more fixed. 

Once you decide on these values, you're ready to create a group for and deploy this template into your Azure subscription. 

Once you have your parameter values ready, you must create a resource group for your template deployment and then deploy the template.

To create the resource group, type azure group create <group name> <location> with the name of the group you want and the datacenter location into which you want to deploy. This happens quickly:

Now to create the deployment, call azure group deployment create and pass: 
 * The template file (if you saved the above JSON template to a local file).
* A template URI (if you want to point at the file in GitHub or some other web address).
* The resource group into which you want to deploy.
* An optional deployment name.

You will be prompted to supply the values of parameters in the "parameters" section of the JSON file. When you have specified all the parameter values, your deployment will begin.
"""))
