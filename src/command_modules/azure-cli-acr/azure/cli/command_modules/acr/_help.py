# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

#pylint: disable=line-too-long

helps['acr'] = """
            type: group
            short-summary: Manage Azure container registries.
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
                - name: List container registries and show the results in a table.
                  text:
                    az acr list -o table
                - name: List container registries in a resource group and the show results in a table.
                  text:
                    az acr list -g MyResourceGroup -o table
            """

helps['acr create'] = """
            type: command
            examples:
                - name: Create a container registry with a new storage account.
                  text:
                    az acr create -n MyRegistry -g MyResourceGroup -l southcentralus
                - name: Create a container registry with an existing storage account.
                  text:
                    az acr create -n MyRegistry -g MyResourceGroup -l southcentralus --storage-account-name MyStorageAccount
            """

helps['acr update'] = """
            type: command
            short-summary: Update a Azure container registry.
            examples:
                - name: Update tags for a container registry.
                  text:
                    az acr update -n MyRegistry --tags key1=value1 key2=value2
                - name: Update the storage account for a container registry.
                  text:
                    az acr update -n MyRegistry --storage-account-name MyStorageAccount
                - name: Enable the administrator user account for a container registry.
                  text:
                    az acr update -n MyRegistry --admin-enabled true
            """

helps['acr repository list'] = """
            type: command
            examples:
                - name: If the administrator user account is enabled, list the repositories in a given container registry. 
                  text:
                    az acr repository list -n MyRegistry
                - name: List the repositories in a given container registry with credentials.
                  text:
                    az acr repository list -n MyRegistry
            """

helps['acr repository show-tags'] = """
            type: command
            examples:
                - name: If the administrator user account is enabled, show the tags of a given repository in a given container registry.
                  text:
                    az acr repository show-tags -n MyRegistry --repository MyRepository
                - name: Show the tags of a given repository in a given container registry with credentials.
                  text:
                    az acr repository show-tags -n MyRegistry --repository MyRepository
            """

helps['acr credential show'] = """
    type: command
    examples:
        - name: Get credentials for a registry.
          text: >
            az acr credential show -g MyResourceGroup -n MyRegistry
"""

helps['acr show'] = """
    type: command
    examples:
        - name: Get the login server for a registry.
          text: >
            az acr show -n MyRegistry --query "loginServer"
"""

helps['acr credential renew'] = """
    type: command
    examples:
        - name: Renew credentials for a registry.
          text: >
            az acr credential renew -g MyResourceGroup -n MyRegistry
"""

helps['acr check-name'] = """
    type: command
    examples:
        - name: Check if a registry name already exists.
          text: >
            az acr check-name -n doesthisnameexist
"""

helps['acr delete'] = """
    type: command
    examples:
        - name: Delete a registry
          text: >
            az acr delete -g MyResourceGroup -n MyRegistry
"""