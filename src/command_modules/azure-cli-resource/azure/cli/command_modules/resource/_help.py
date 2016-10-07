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
helps['resource group deployment operation'] = """
    type: group
    short-summary: Commands to manage deployment operations
"""
helps['resource provider'] = """
    type: group
    short-summary: Commands to manage resource providers
"""

helps['tag'] = """
    type: group
    short-summary: Manage resource tags
"""
