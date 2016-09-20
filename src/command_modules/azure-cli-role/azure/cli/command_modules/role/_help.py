#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['ad sp create-for-rbac'] = """
            examples:
                - name: Create with defaults
                  text: az ad sp create-for-rbac
                - name: Create with a custom name
                  text: az ad sp create-for-rbac -n "http://my-app"
                - name: Create role assignments at the same time
                  text: az ad sp create-for-rbac -n "http://my-app" --role contributor --resource-ids /subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/mygroup /subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/my-another-group
            """

helps['role'] = """
    type: group
    short-summary: Commands to manage Azure Active Directory (AAD) roles
"""
helps['role assignment'] = """
    type: group
    short-summary: Commands to manage AAD role assignments
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
