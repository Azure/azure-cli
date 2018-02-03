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
"""

helps['acr list'] = """
    type: command
    short-summary: Lists available container registries for a subscription or resource group.
"""

helps['acr create'] = """
    type: command
    short-summary: Creates a container registry.
"""

helps['acr delete'] = """
    type: command
    short-summary: Deletes a container registry.
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
"""

helps['acr show-usage'] = """
    type: command
    short-summary: Get the quota usages for a container registry.
"""

helps['acr credential show'] = """
    type: command
    short-summary: Get the login credentials for a container registry.
    examples:
        - name: Get the username and password used to log into a container registry.
          text: >
            az acr credential show -n MyRegistry --query {user:username, password:passwords[0].value}
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
"""

helps['acr repository show-tags'] = """
    type: command
    short-summary: Show tags for a repository in a container registry.
"""

helps['acr repository show-manifests'] = """
    type: command
    short-summary: Show manifests of a repository in a container registry.
"""

helps['acr repository delete'] = """
    type: command
    short-summary: Delete a repository, manifest, or tag in a container registry.
    parameters:
        - name: --manifest
          populator-commands:
            - az acr repository show-manifests
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
        - name: Delete a manifest using a sha256 based digest. This also deletes any associated layer data and all tags referencing the manifest.
          text:
            az acr repository delete -n MyRegistry --repository MyRepository --manifest sha256:abc123
"""

helps['acr webhook list'] = """
    type: command
    short-summary: List all of the webhooks for a container registry.
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
"""

helps['acr webhook show'] = """
    type: command
    short-summary: Get the details of a webhook.
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
"""

helps['acr webhook ping'] = """
    type: command
    short-summary: Trigger a ping event for a webhook.
"""

helps['acr webhook list-events'] = """
    type: command
    short-summary: List recent events for a webhook.
"""

helps['acr replication list'] = """
    type: command
    short-summary: List all of the replications for a container registry.
"""

helps['acr replication create'] = """
    type: command
    short-summary: Create a replication for a container registry.
"""

helps['acr replication delete'] = """
    type: command
    short-summary: Delete a replication for a container registry.
"""

helps['acr replication show'] = """
    type: command
    short-summary: Get the details of a replication.
"""

helps['acr replication update'] = """
    type: command
    short-summary: Updates a replication.
    examples:
        - name: Update tags for a replication
          text: >
            az acr replication update -n MyReplication -r MyRegistry --tags key1=value1 key2=value2
"""
