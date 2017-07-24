# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['acr'] = """
    type: group
    short-summary: Manage Azure Container Registries.
    """

helps['acr credential'] = """
    type: group
    short-summary: Manage login credentials for Azure container registries.
    """

helps['acr repository'] = """
    type: group
    short-summary: Manage repositories for Azure container registries.
    """

helps['acr webhook'] = """
    type: group
    short-summary: Manage webhooks for Azure container registries.
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
        - name: Create a managed container registry. Applicable to Managed SKU.
          text: >
            az acr create -n MyRegistry -g MyResourceGroup --sku Managed_Standard
        - name: Create a container registry with a new storage account. Applicable to Basic SKU.
          text: >
            az acr create -n MyRegistry -g MyResourceGroup --sku Basic
"""

helps['acr delete'] = """
    type: command
    short-summary: Deletes a container registry.
    examples:
        - name: Delete a container registry.
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

helps['acr login'] = """
    type: command
    short-summary: Login to a container registry through Docker.
    examples:
        - name: Login to a container registry
          text: >
            az acr login -n MyRegistry
"""

helps['acr show-usage'] = """
    type: command
    short-summary: Gets the quota usages for the specified container registry.
    examples:
        - name: Get the quota usages for a container registry.
          text: >
            az acr show-usage -n MyRegistry
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
        - name: List repositories in a given container registry.
          text:
            az acr repository list -n MyRegistry
"""

helps['acr repository show-tags'] = """
    type: command
    short-summary: Shows tags of a given repository in the specified container registry.
    examples:
        - name: Show tags of a given repository in a given container registry.
          text:
            az acr repository show-tags -n MyRegistry --repository MyRepository
"""

helps['acr repository show-manifests'] = """
    type: command
    short-summary: Shows manifests of a given repository in the specified container registry.
    examples:
        - name: Show manifests of a given repository in a given container registry.
          text:
            az acr repository show-manifests -n MyRegistry --repository MyRepository
"""

helps['acr repository delete'] = """
    type: command
    short-summary: Deletes a repository or a manifest/tag from the given repository in the specified container registry.
    examples:
        - name: Delete a repository from the specified container registry.
          text:
            az acr repository delete -n MyRegistry --repository MyRepository
        - name: Delete a tag from the given repository. This operation does not delete the manifest referenced by the tag or associated layer data.
          text:
            az acr repository delete -n MyRegistry --repository MyRepository --tag MyTag
        - name: Delete the manifest referenced by a tag. This operation also deletes associated layer data and all other tags referencing the manifest.
          text:
            az acr repository delete -n MyRegistry --repository MyRepository --tag MyTag --manifest
        - name: Delete a manfiest from the given repository. This operation also deletes associated layer data and all tags referencing the manifest.
          text:
            az acr repository delete -n MyRegistry --repository MyRepository --manifest MyManifest
"""

helps['acr webhook list'] = """
    type: command
    short-summary: Lists all the webhooks for the specified container registry.
    examples:
        - name: List webhooks and show the results in a table.
          text: >
            az acr webhook list -r MyRegistry -o table
"""

helps['acr webhook create'] = """
    type: command
    short-summary: Creates a webhook for a container registry.
    examples:
        - name: Create a webhook for a container registry that will deliver Docker push and delete events to the specified service URI.
          text: >
            az acr webhook create -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push delete
        - name: Create a webhook for a container registry that will deliver Docker push events to the specified service URI with Basic authentication header.
          text: >
            az acr webhook create -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push --headers "Authorization=Basic 000000"
"""

helps['acr webhook delete'] = """
    type: command
    short-summary: Deletes a webhook from a container registry.
    examples:
        - name: Delete a webhook from a container registry.
          text: >
            az acr webhook delete -n MyWebhook -r MyRegistry
"""

helps['acr webhook show'] = """
    type: command
    short-summary: Gets the properties of the specified webhook.
    examples:
        - name: Get the properties of the specified webhook.
          text: >
            az acr webhook show -n MyWebhook -r MyRegistry
"""

helps['acr webhook update'] = """
    type: command
    short-summary: Updates a webhook.
    examples:
        - name: Update headers for a webhook
          text: >
            az acr webhook update -n MyWebhook -r MyRegistry --headers "Authorization=Basic 000000"
        - name: Update service URI and actions for a webhook
          text: >
            az acr webhook update -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push delete
        - name: Disable a webhook
          text: >
            az acr webhook update -n MyWebhook -r MyRegistry --status disabled
"""

helps['acr webhook get-config'] = """
    type: command
    short-summary: Gets the configuration of service URI and custom headers for the webhook.
    examples:
        - name: Get service URI and headers for the webhook.
          text: >
            az acr webhook get-config -n MyWebhook -r MyRegistry
"""

helps['acr webhook ping'] = """
    type: command
    short-summary: Triggers a ping event to be sent to the webhook.
    examples:
        - name: Triggers a ping event to be sent to the webhook.
          text: >
            az acr webhook ping -n MyWebhook -r MyRegistry
"""

helps['acr webhook list-events'] = """
    type: command
    short-summary: Lists recent events for the specified webhook.
    examples:
        - name: List recent events for the specified webhook.
          text: >
            az acr webhook list-events -n MyWebhook -r MyRegistry
"""
