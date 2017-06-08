# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['acr'] = """
    type: group
    short-summary: Manage Azure container registries.
    """

helps['acr credential'] = """
    type: group
    short-summary: Manage login credentials for Azure container registries.
    """

helps['acr repository'] = """
    type: group
    short-summary: Manage repositories for Azure container registries.
    """

helps['acr check-name'] = """
    type: command
    short-summary: Checks whether the container registry name is available for use.
    examples:
        - name: Check if a registry name already exists.
          text: >
            az acr check-name -n doesthisnameexist
"""

helps['acr list'] = """
    type: command
    short-summary: Lists all the container registries under the current subscription.
    examples:
        - name: List container registries and show the results in a table.
          text: >
            az acr list -o table
        - name: List container registries in a resource group and show the results in a table.
          text: >
            az acr list -g MyResourceGroup -o table
"""

helps['acr create'] = """
    type: command
    short-summary: Creates a container registry.
    examples:
        - name: Create a container registry with a new storage account.
          text: >
            az acr create -n MyRegistry -g MyResourceGroup -l southcentralus --sku Basic
"""

helps['acr delete'] = """
    type: command
    short-summary: Deletes a container registry.
    examples:
        - name: Delete a container registry
          text: >
            az acr delete -n MyRegistry
"""

helps['acr show'] = """
    type: command
    short-summary: Gets the properties of the specified container registry.
    examples:
        - name: Get the login server for a container registry.
          text: >
            az acr show -n MyRegistry --query loginServer
"""

helps['acr update'] = """
    type: command
    short-summary: Updates a container registry.
    examples:
        - name: Update tags for a container registry.
          text: >
            az acr update -n MyRegistry --tags key1=value1 key2=value2
        - name: Update the storage account for a container registry.
          text: >
            az acr update -n MyRegistry --storage-account-name MyStorageAccount
        - name: Enable the administrator user account for a container registry.
          text: >
            az acr update -n MyRegistry --admin-enabled true
"""

helps['acr credential show'] = """
    type: command
    short-summary: Gets the login credentials for the specified container registry.
    examples:
        - name: Get the login credentials for a container registry.
          text: >
            az acr credential show -n MyRegistry
        - name: Get the username used to log into a container registry.
          text: >
            az acr credential show -n MyRegistry --query username
        - name: Get one of the passwords used to log into a container registry.
          text: >
            az acr credential show -n MyRegistry --query passwords[0].value
"""

helps['acr credential renew'] = """
    type: command
    short-summary: Regenerates one of the login credentials for the specified container registry.
    examples:
        - name: Renew the second password for a container registry.
          text: >
            az acr credential renew -n MyRegistry --password-name password2
"""

helps['acr repository list'] = """
    type: command
    short-summary: Lists repositories in the specified container registry.
    examples:
        - name: List repositories in a given container registry. Enter login credentials in the prompt if admin user is disabled.
          text:
            az acr repository list -n MyRegistry
"""

helps['acr repository show-tags'] = """
    type: command
    short-summary: Shows tags of a given repository in the specified container registry.
    examples:
        - name: Show tags of a given repository in a given container registry. Enter login credentials in the prompt if admin user is disabled.
          text:
            az acr repository show-tags -n MyRegistry --repository MyRepository
"""
