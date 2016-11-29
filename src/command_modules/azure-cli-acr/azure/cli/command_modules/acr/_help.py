# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

#pylint: disable=line-too-long

helps['acr'] = """
            type: group
            short-summary: Commands to manage Azure container registries.
            """

helps['acr credential'] = """
            type: group
            short-summary: Manage administrator login credentials for Azure container registries.
            """

helps['acr repository'] = """
            type: group
            short-summary: Manage repositories for Azure container registries.
            """

helps['acr list'] = """
            type: command
            examples:
                - name: List container registries and show result in a table.
                  text:
                    az acr list -o table
                - name: List container registries in a resource group and show result in a table.
                  text:
                    az acr list -g myResourceGroup -o table
            """

helps['acr create'] = """
            type: command
            examples:
                - name: Create a container registry with a new storage account.
                  text:
                    az acr create -n myRegistry -g myResourceGroup -l southcentralus
                - name: Create a container registry with an existing storage account.
                  text:
                    az acr create -n myRegistry -g myResourceGroup -l southcentralus --storage-account-name myStorageAccount
            """

helps['acr update'] = """
            type: command
            short-summary: Updates a container registry.
            examples:
                - name: Update tags for a container registry
                  text:
                    az acr update -n myRegistry --tags key1=value1 key2=value2
                - name: Update storage account for a container registry
                  text:
                    az acr update -n myRegistry --storage-account-name myStorageAccount
                - name: Enable admin user for a container registry
                  text:
                    az acr update -n myRegistry --admin-enabled true
            """

helps['acr repository list'] = """
            type: command
            examples:
                - name: List repositories in a given container registry if admin user is enabled
                  text:
                    az acr repository list -n myRegistry
                - name: List repositories in a given container registry with credentials
                  text:
                    az acr repository list -n myRegistry -u myUsername -p myPassword
            """

helps['acr repository show-tags'] = """
            type: command
            examples:
                - name: Show tags of a given repository in a given container registry if admin user is enabled
                  text:
                    az acr repository show-tags -n myRegistry --repository myRepository
                - name: Show tags of a given repository in a given container registry with credentials
                  text:
                    az acr repository show-tags -n myRegistry --repository myRepository -u myUsername -p myPassword
            """
