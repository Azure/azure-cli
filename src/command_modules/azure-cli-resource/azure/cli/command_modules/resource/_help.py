#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long
helps['resource policy'] = """
    type: group
    short-summary: Commands to manage resource policies
"""
helps['resource policy definition'] = """
    type: group
    short-summary: manage resource policy definitions
"""
helps['resource policy definition create'] = """
            type: command
            short-summary: Creates a policy definition
            parameters:
                - name: --rules
                  type: string
                  short-summary: 'JSON formatted string or a path to a file with such content'
            examples:
                - name: Create a policy with following rules
                  text: |
                        {
                            "if":
                            {
                                "source": "action",
                                "equals": "Microsoft.Storage/storageAccounts/write"
                            },
                            "then":
                            {
                                "effect": "deny"
                            }
                        }
            """
helps['resource policy definition delete'] = """
    type: command
    short-summary: deletes a policy definition
"""
helps['resource policy definition update'] = """
    type: command
    short-summary: updates a policy definition
"""
helps['resource policy definition list'] = """
    type: command
    short-summary: lists policy definitions
"""
helps['resource policy assignment'] = """
    type: group
    short-summary: manage resource policy assignments
"""
helps['resource policy assignment create'] = """
    type: command
    short-summary: creates a resource policy assignment
"""
helps['resource policy assignment delete'] = """
    type: command
    short-summary: deletes a resource policy assignment
"""
helps['resource policy assignment show'] = """
    type: command
    short-summary: shows a resource policy assignment
"""
helps['resource policy assignment list'] = """
    type: command
    short-summary: list resource policy assignments
"""
helps['resource'] = """
    type: group
    short-summary: Generic commands to manage Azure resources
"""
helps['resource show'] = """
    type: command
    short-summary: display a resource detail
    examples:
        - name: show a virtual machine
          text: >
            az vm show -g mygroup -n myvm --resource-type "Microsoft.Compute/virtualMachines"
        - name: show a webapp
          text: >
            az resource show -g mygroup -n mywebapp --resource-type "Microsoft.web/sites"
"""
helps['resource feature'] = """
    type: group
    short-summary: Commands to manage resource provider features, such as previews
"""
helps['resource group'] = """
    type: group
    short-summary: Commands to manage resource groups
"""
helps['resource group deployment'] = """
    type: group
    short-summary: Commands to execute or manage ARM deployments
"""
helps['resource group deployment create'] = """
    type: command
    short-summary: start a deployment
    examples:
        - name: create a deployment from a remote template file
          text: >
            az resource group deployment create -g mygroup --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
        - name: create a deployment from a local template file and use parameter values in string 
          text: >
            az resource group deployment create -g mygroup --template-file azuredeploy.json --parameters "{\\"location\\": {\\"value\\": \\"westus\\"}}"
"""
helps['resource group deployment operation'] = """
    type: group
    short-summary: Commands to manage deployment operations
"""
helps['provider'] = """
    type: group
    short-summary: Manage resource providers
"""
helps['provider register'] = """
    type: command
    short-summary: Register a provider
"""
helps['provider unregister'] = """
    type: command
    short-summary: Unregister a provider
"""
helps['tag'] = """
    type: group
    short-summary: Manage resource tags
"""
