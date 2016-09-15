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
                  text: az ad sp create-for-rbac -n "http://my-app" --resource-ids /subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/mygroup 
            """