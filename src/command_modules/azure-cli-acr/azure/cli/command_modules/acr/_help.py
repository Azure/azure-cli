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
    short-summary: Manage login credentials for Azure Container Registries.
    """

helps['acr repository'] = """
    type: group
    short-summary: Manage repositories for Azure Container Registries.
    """

helps['acr webhook'] = """
    type: group
    short-summary: Manage webhooks for Azure Container Registries.
    """

helps['acr replication'] = """
    type: group
    short-summary: Manage replications for Azure Container Registries.
    """

helps['acr check-name'] = """
    type: command
    short-summary: Checks if a container registry name is available for use.
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
        - name: Create a managed container registry with the Standard SKU.
          text: >
            az acr create -n MyRegistry -g MyResourceGroup --sku Standard
        - name: Create a container registry with a new storage account with the Classic SKU.
          text: >
            az acr create -n MyRegistry -g MyResourceGroup --sku Classic
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
    short-summary: Get the details of a container registry.
    examples:
        - name: Get the login server for a container registry.
          text: >
            az acr show -n MyRegistry --query loginServer
"""

helps['acr update'] = """
    type: command
    short-summary: Update a container registry.
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
    short-summary: Log in to a container registry through Docker.
    examples:
        - name: Log in to a container registry
          text: >
            az acr login -n MyRegistry
"""

helps['acr show-usage'] = """
    type: command
    short-summary: Get the quota usages for a container registry.
    examples:
        - name: Get the quota usages for a container registry.
          text: >
            az acr show-usage -n MyRegistry
"""

helps['acr credential show'] = """
    type: command
    short-summary: Get the login credentials for a container registry.
    examples:
        - name: Get the login credentials for a container registry.
          text: >
            az acr credential show -n MyRegistry
        - name: Get the username used to log into a container registry.
          text: >
            az acr credential show -n MyRegistry --query username
        - name: Get a password used to log into a container registry.
          text: >
            az acr credential show -n MyRegistry --query passwords[0].value
"""

helps['acr credential renew'] = """
    type: command
    short-summary: Regenerate login credentials for a container registry.
    examples:
        - name: Renew the second password for a container registry.
          text: >
            az acr credential renew -n MyRegistry --password-name password2
"""

helps['acr repository list'] = """
    type: command
    short-summary: List repositories in a container registry.
    examples:
        - name: List repositories in a given container registry.
          text:
            az acr repository list -n MyRegistry
"""

helps['acr repository show-tags'] = """
    type: command
    short-summary: Show tags for a repository in a container registry.
    examples:
        - name: Show tags of a repository in a container registry.
          text:
            az acr repository show-tags -n MyRegistry --repository MyRepository
"""

helps['acr repository show-manifests'] = """
    type: command
    short-summary: Show manifests of a repository in a container registry.
    examples:
        - name: Show manifests of a repository in a container registry.
          text:
            az acr repository show-manifests -n MyRegistry --repository MyRepository
"""

helps['acr repository delete'] = """
    type: command
    short-summary: Delete a repository, manifest, or tag in a container registry.
    examples:
        - name: Delete a repository from a container registry.
          text:
            az acr repository delete -n MyRegistry --repository MyRepository
        - name: Delete a tag from a repository. This does not delete the manifest referenced by the tag or any associated layer data.
          text:
            az acr repository delete -n MyRegistry --repository MyRepository --tag MyTag
        - name: Delete the manifest referenced by a tag. This also deletes any associated layer data and all other tags referencing the manifest.
          text:
            az acr repository delete -n MyRegistry --repository MyRepository --tag MyTag --manifest
        - name: Delete a manfiest from a repository. This also deletes any associated layer data and all tags referencing the manifest.
          text:
            az acr repository delete -n MyRegistry --repository MyRepository --manifest MyManifest
"""

helps['acr webhook list'] = """
    type: command
    short-summary: List all of the webhooks for a container registry.
    examples:
        - name: List webhooks and show the results in a table.
          text: >
            az acr webhook list -r MyRegistry -o table
"""

helps['acr webhook create'] = """
    type: command
    short-summary: Create a webhook for a container registry.
    examples:
        - name: Create a webhook for a container registry that will deliver Docker push and delete events to a service URI.
          text: >
            az acr webhook create -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push delete
        - name: Create a webhook for a container registry that will deliver Docker push events to a service URI with a basic authentication header.
          text: >
            az acr webhook create -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push --headers "Authorization=Basic 000000"
"""

helps['acr webhook delete'] = """
    type: command
    short-summary: Delete a webhook from a container registry.
    examples:
        - name: Delete a webhook from a container registry.
          text: >
            az acr webhook delete -n MyWebhook -r MyRegistry
"""

helps['acr webhook show'] = """
    type: command
    short-summary: Get the details of a webhook.
    examples:
        - name: Get the details of a webhook.
          text: >
            az acr webhook show -n MyWebhook -r MyRegistry
"""

helps['acr webhook update'] = """
    type: command
    short-summary: Update a webhook.
    examples:
        - name: Update headers for a webhook.
          text: >
            az acr webhook update -n MyWebhook -r MyRegistry --headers "Authorization=Basic 000000"
        - name: Update the service URI and actions for a webhook.
          text: >
            az acr webhook update -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push delete
        - name: Disable a webhook.
          text: >
            az acr webhook update -n MyWebhook -r MyRegistry --status disabled
"""

helps['acr webhook get-config'] = """
    type: command
    short-summary: Get the service URI and custom headers for the webhook.
    examples:
        - name: Get the configuration information for a webhook.
          text: >
            az acr webhook get-config -n MyWebhook -r MyRegistry
"""

helps['acr webhook ping'] = """
    type: command
    short-summary: Trigger a ping event for a webhook.
    examples:
        - name: Trigger a ping event for a webhook.
          text: >
            az acr webhook ping -n MyWebhook -r MyRegistry
"""

helps['acr webhook list-events'] = """
    type: command
    short-summary: List recent events for a webhook.
    examples:
        - name: List recent events for a webhook.
          text: >
            az acr webhook list-events -n MyWebhook -r MyRegistry
"""

helps['acr replication list'] = """
    type: command
    short-summary: List all of the replications for a container registry.
    examples:
        - name: List replications and show the results in a table.
          text: >
            az acr replication list -r MyRegistry -o table
"""

helps['acr replication create'] = """
    type: command
    short-summary: Create a replication for a container registry.
    examples:
        - name: Create a replication for a container registry.
          text: >
            az acr replication create -r MyRegistry -l westus
"""

helps['acr replication delete'] = """
    type: command
    short-summary: Delete a replication from a container registry.
    examples:
        - name: Delete a replication from a container registry.
          text: >
            az acr replication delete -n MyReplication -r MyRegistry
"""

helps['acr replication show'] = """
    type: command
    short-summary: Get the details of a replication.
    examples:
        - name: Get the details of a replication.
          text: >
            az acr replication show -n MyReplication -r MyRegistry
"""

helps['acr replication update'] = """
    type: command
    short-summary: Updates a replication.
    examples:
        - name: Update tags for a replication
          text: >
            az acr replication update -n MyReplication -r MyRegistry --tags key1=value1 key2=value2
"""
