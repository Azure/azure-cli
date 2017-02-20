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
                    az acr list -g my_rg -o table
            """

helps['acr create'] = """
            type: command
            examples:
                - name: Create a container registry with a new storage account.
                  text:
                    az acr create -n my_registry -g my_rg -l southcentralus
                - name: Create a container registry with an existing storage account.
                  text:
                    az acr create -n my_registry -g my_rg -l southcentralus --storage-account-name my_storage_account
            """

helps['acr update'] = """
            type: command
            short-summary: Update a Azure container registry.
            examples:
                - name: Update tags for a container registry.
                  text:
                    az acr update -n my_registry --tags key1=value1 key2=value2
                - name: Update the storage account for a container registry.
                  text:
                    az acr update -n my_registry --storage-account-name my_storage_account
                - name: Enable the administrator user account for a container registry.
                  text:
                    az acr update -n my_registry --admin-enabled true
            """

helps['acr repository list'] = """
            type: command
            examples:
                - name: If the administrator user account is enabled, list the repositories in a given container registry. 
                  text:
                    az acr repository list -n my_registry
                - name: List the repositories in a given container registry with credentials.
                  text:
                    az acr repository list -n my_registry -u my_username -p my_p
            """

helps['acr repository show-tags'] = """
            type: command
            examples:
                - name: If the administrator user account is enabled, show the tags of a given repository in a given container registry.
                  text:
                    az acr repository show-tags -n my_registry --repository my_repository
                - name: Show the tags of a given repository in a given container registry with credentials.
                  text:
                    az acr repository show-tags -n my_registry --repository my_repository -u my_username -p my_p
            """
