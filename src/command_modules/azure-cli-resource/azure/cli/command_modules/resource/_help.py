# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long
helps['policy'] = """
    type: group
    short-summary: Commands to manage resource policies
"""
helps['policy definition'] = """
    type: group
    short-summary: manage resource policy definitions
"""
helps['policy definition create'] = """
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
helps['policy definition delete'] = """
    type: command
    short-summary: deletes a policy definition
"""
helps['policy definition update'] = """
    type: command
    short-summary: updates a policy definition
"""
helps['policy definition list'] = """
    type: command
    short-summary: lists policy definitions
"""
helps['policy assignment'] = """
    type: group
    short-summary: manage resource policy assignments
"""
helps['policy assignment create'] = """
    type: command
    short-summary: creates a resource policy assignment
"""
helps['policy assignment delete'] = """
    type: command
    short-summary: deletes a resource policy assignment
"""
helps['policy assignment show'] = """
    type: command
    short-summary: shows a resource policy assignment
"""
helps['policy assignment list'] = """
    type: command
    short-summary: list resource policy assignments
"""
helps['resource'] = """
    type: group
    short-summary: Generic commands to manage Azure resources
"""
helps['resource list'] = """
    type: command
    short-summary: list resource
    examples:
        - name: list all resource in a region
          text: >
            az resource list --location westus
        - name: list resource with a name
          text: >
            az resource list --name thename
        - name: list resources with a tag
          text: >
             az resource list --tag something
        - name: list resource with a tag with a particular prefix
          text: >
            az resource list --tag some*
        - name: list resource with a tag value
          text: >
            az resource list --tag something=else
"""

helps['resource show'] = """
    type: command
    short-summary: display a resource detail
    long-summary: Get details of a resource like /subscriptions/0000/resourceGroups/myGroup/providers/Microsoft.Provider/resA/myA/resB/myB/resC/myC
    examples:
        - name: show a virtual machine
          text: >
            az vm show -g mygroup -n myvm --resource-type "Microsoft.Compute/virtualMachines"
        - name: show a webapp using resource id
          text: >
            az resource show --id /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/myGroup/providers/Microsoft.Web/sites/myWebapp
        - name: show a subnet
          text: >
            az resource show -g mygroup -n mysubnet --namespace microsoft.network --parent virtualnetworks/myvnet --resource-type subnets
        - name: show a subnet using id
          text: >
            az resource show --id /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/myGroup/providers/Microsoft.Network/virtualNetworks/myvnet/subnets/mysubnet
        - name: show an app gateway path rule
          text: >
            az resource show -g myGroup --namespace Microsoft.Network --parent applicationGateways/ag1/urlPathMaps/map1 --resource-type pathRules -n rule1  
"""

helps['resource delete'] = """
    type: command
    short-summary: delete a resource. Reference the examples for help with arguments.
    long-summary: delete a resource like /subscriptions/0000/resourceGroups/myGroup/providers/Microsoft.Provider/resA/myA/resB/myB/resC/myC
    examples:
        - name: delete a virtual machine
          text: >
            az vm delete -g mygroup -n myvm --resource-type "Microsoft.Compute/virtualMachines"
        - name: delete a webapp using resource id
          text: >
            az resource delete --id /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/myGroup/providers/Microsoft.Web/sites/myWebapp
        - name: delete a subnet using id
          text: >
            az resource delete --id /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/myGroup/providers/Microsoft.Network/virtualNetworks/myvnet/subnets/mysubnet
"""

helps['resource tag'] = """
    type: command
    short-summary: tag a resource. Reference the examples for help with arguments.
    long-summary: tag a resource like /subscriptions/0000/resourceGroups/myGroup/providers/Microsoft.Provider/resA/myA/resB/myB/resC/myC
    examples:
        - name: tag a virtual machine
          text: >
            az resource tag --tags vmlist=vm1 -g mygroup -n myvm --resource-type "Microsoft.Compute/virtualMachines"
        - name: tag a webapp using resource id
          text: >
            az resource tag --tags vmlist=vm1 --id /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/myGroup/providers/Microsoft.Web/sites/myWebapp
"""

helps['resource update'] = """
    type: command
    short-summary: update a resource
"""

helps['feature'] = """
    type: group
    short-summary: Commands to manage resource provider features, such as previews
"""
helps['group'] = """
    type: group
    short-summary: Commands to manage resource groups
"""
helps['group deployment'] = """
    type: group
    short-summary: Commands to execute or manage ARM deployments
"""
helps['group deployment create'] = """
    type: command
    short-summary: start a deployment
    examples:
        - name: create a deployment from a remote template file
          text: >
            az group deployment create -g mygroup --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
        - name: create a deployment from a local template file and use parameter values in string 
          text: >
            az group deployment create -g mygroup --template-file azuredeploy.json --parameters "{\\"location\\": {\\"value\\": \\"westus\\"}}"
"""
helps['group deployment operation'] = """
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
