# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['ad sp create-for-rbac'] = """
            examples:
                - name: Create with defaults
                  text: az ad sp create-for-rbac
                - name: Create with a custom name
                  text: az ad sp create-for-rbac -n "http://my-app"
                - name: Create role assignments at the same time
                  text: az ad sp create-for-rbac -n "http://my-app" --role contributor --scopes /subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/mygroup /subscriptions/11111111-2222-3333-4444-666666666666/resourceGroups/my-another-group
                - name: Login with this service principal
                  text: az login --service-principal -u <name> -p <password> --tenant <tenant>
                - name: Reset credentials on expiration
                  text: az ad sp reset-credentials --name <name>
                - name: Create role assignments
                  text: az role assignment create --assignee <name> --role Contributor
                - name: Revoke the service principal when done with it
                  text: az ad app delete --id <name>
            """

helps['role'] = """
    type: group
    short-summary: Use role assignments to manage access to your Azure resources
"""
helps['role assignment'] = """
    type: group
    short-summary: Manage role assignments
"""
helps['role assignment create'] = """
    type: command
    short-summary: Create a new role assignment
"""
helps['role assignment delete'] = """
    type: command
    short-summary: Delete role assignments
"""
helps['role assignment list'] = """
    type: command
    short-summary: list role assignments
"""
helps['role definition'] = """
    type: group
    short-summary: Manage role definitions
"""

helps['role definition create'] = """
    type: command
    short-summary: Create a custom role definition
    parameters: 
        - name: --role-definition
          type: string
          short-summary: 'JSON formatted string or a path to a file with such content'
    examples:
        - name: Create a role with following definition content
          text: |
                {
                    "Name": "Contoso On-call",
                    "Description": "Can monitor compute, network and storage, and restart virtual machines",
                    "Actions": [
                        "Microsoft.Compute/*/read",
                        "Microsoft.Compute/virtualMachines/start/action",
                        "Microsoft.Compute/virtualMachines/restart/action",
                        "Microsoft.Network/*/read",
                        "Microsoft.Storage/*/read",
                        "Microsoft.Authorization/*/read",
                        "Microsoft.Resources/subscriptions/resourceGroups/read",
                        "Microsoft.Resources/subscriptions/resourceGroups/resources/read",
                        "Microsoft.Insights/alertRules/*",
                        "Microsoft.Support/*"
                    ],
                    "AssignableScopes": ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"]
                }
"""

helps['role definition delete'] = """
    type: command
    short-summary: Delete a role definition
"""
helps['role definition list'] = """
    type: command
    short-summary: list role definitions
"""
helps['role definition update'] = """
    type: command
    short-summary: update a role definition
"""
helps['role definition create'] = """
            type: command
            parameters: 
                - name: --role-definition
                  type: string
                  short-summary: 'JSON formatted string or a path to a file with such content'
            examples:
                - name: Create a role with following definition content
                  text: |
                        {
                            "Name": "Contoso On-call",
                            "Description": "Can monitor compute, network and storage, and restart virtual machines",
                            "Actions": [
                                "Microsoft.Compute/*/read",
                                "Microsoft.Compute/virtualMachines/start/action",
                                "Microsoft.Compute/virtualMachines/restart/action",
                                "Microsoft.Network/*/read",
                                "Microsoft.Storage/*/read",
                                "Microsoft.Authorization/*/read",
                                "Microsoft.Resources/subscriptions/resourceGroups/read",
                                "Microsoft.Resources/subscriptions/resourceGroups/resources/read",
                                "Microsoft.Insights/alertRules/*",
                                "Microsoft.Support/*"
                            ],
                            "AssignableScopes": ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"]
                        }

            """
helps['ad'] = """
    type: group
    short-summary: Synchronize on-premises directories and manage Azure Active Directory (AAD) resources
"""
helps['ad app'] = """
    type: group
    short-summary: Manages AAD applications
"""
helps['ad group'] = """
    type: group
    short-summary: Manages AAD groups
"""
helps['ad sp'] = """
    type: group
    short-summary: Manages AAD service principals for automation authentication
"""
helps['ad user'] = """
    type: group
    short-summary: Manages AAD users and user authentication
"""
