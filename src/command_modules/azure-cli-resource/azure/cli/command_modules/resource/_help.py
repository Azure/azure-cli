#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['resource policy create'] = """
            type: command
            short-summary: Create a policy 
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

helps['resource'] = """
    type: group
    short-summary: Generic commands to managing Azure resources
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
helps['resource policy'] = """
    type: group
    short-summary: Commands to manage resource policies
"""
helps['resource policy assignment'] = """
    type: group
    short-summary: Commands to manage resource policy assignments
"""
helps['resource provider'] = """
    type: group
    short-summary: Commands to manage resource providers
"""

helps['tag'] = """
    type: group
    short-summary: Manage and track resources quickly with tags
"""