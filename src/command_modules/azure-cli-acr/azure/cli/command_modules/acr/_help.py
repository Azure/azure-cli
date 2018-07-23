# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['acr'] = """
    type: group
    short-summary: Manage Azure Container Registries for private registries within Azure.
    """

helps['acr credential'] = """
    type: group
    short-summary: Manage login credentials for Azure Container Registries.
    """

helps['acr repository'] = """
    type: group
    short-summary: Manage repositories (image names) for Azure Container Registries.
    """

helps['acr webhook'] = """
    type: group
    short-summary: Manage webhooks for Azure Container Registries.
    """

helps['acr replication'] = """
    type: group
    short-summary: Manage replications of Azure Container Registries across multiple regions.
    """

helps['acr build-task'] = """
    type: group
    short-summary: Manage build definitions, which can be triggered by git commits or base image updates.
    """

helps['acr check-name'] = """
    type: command
    short-summary: Checks if a container registry name is valid and available for use.
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
    short-summary: Log in to a container registry through the Docker CLI.
    long-summary: Docker must be installed on your machine.
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
        - name: Get the username used to log in to a container registry.
          text: >
            az acr credential show -n MyRegistry --query username
        - name: Get a password used to log in to a container registry.
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
        - name: Show the detailed information of tags of a repository in a container registry.
          text:
            az acr repository show-tags -n MyRegistry --repository MyRepository --detail
        - name: Show the detailed information of the latest 10 tags ordered by timestamp of a repository in a container registry.
          text:
            az acr repository show-tags -n MyRegistry --repository MyRepository --top 10 --orderby time_desc --detail
"""

helps['acr repository show-manifests'] = """
    type: command
    short-summary: Show manifests of a repository in a container registry.
    examples:
        - name: Show manifests of a repository in a container registry.
          text:
            az acr repository show-manifests -n MyRegistry --repository MyRepository
        - name: Show the latest 10 manifests ordered by timestamp of a repository in a container registry.
          text:
            az acr repository show-manifests -n MyRegistry --repository MyRepository --top 10 --orderby time_desc
        - name: Show the detailed information of the latest 10 manifests ordered by timestamp of a repository in a container registry.
          text:
            az acr repository show-manifests -n MyRegistry --repository MyRepository --top 10 --orderby time_desc --detail
"""

helps['acr repository show'] = """
    type: command
    short-summary: Get the attributes of a repository or image in a container registry.
    examples:
        - name: Get the attributes of the repository 'hello-world'.
          text:
            az acr repository show -n MyRegistry --repository hello-world
        - name: Get the attributes of the image referenced by tag 'hello-world:latest'.
          text:
            az acr repository show -n MyRegistry --image hello-world:latest
        - name: Get the attributes of the image referenced by digest 'hello-world@sha256:abc123'.
          text:
            az acr repository show -n MyRegistry --image hello-world@sha256:abc123
"""

helps['acr repository update'] = """
    type: command
    short-summary: Update the attributes of a repository or image in a container registry.
    examples:
        - name: Update the attributes of the repository 'hello-world' to disable write operation.
          text:
            az acr repository update -n MyRegistry --repository hello-world --write-enabled false
        - name: Update the attributes of the image referenced by tag 'hello-world:latest' to disable write operation.
          text:
            az acr repository update -n MyRegistry --image hello-world:latest --write-enabled false
        - name: Update the attributes of the image referenced by digest 'hello-world@sha256:abc123' to disable write operation.
          text:
            az acr repository update -n MyRegistry --image hello-world@sha256:abc123 --write-enabled false
"""

helps['acr repository delete'] = """
    type: command
    short-summary: Delete a repository or image in a container registry.
    long-summary: This command deletes all associated layer data that are not referenced by any other manifest in the container registry.
    examples:
        - name: Delete a repository from a container registry. This deletes all manifests and tags under 'hello-world'.
          text:
            az acr repository delete -n MyRegistry --repository hello-world
        - name: Delete an image by tag. This deletes the manifest referenced by 'hello-world:latest' and all other tags referencing the manifest.
          text:
            az acr repository delete -n MyRegistry --image hello-world:latest
        - name: Delete an image by sha256-based manifest digest. This deletes the manifest identified by 'hello-world@sha256:abc123' and all tags referencing the manifest.
          text:
            az acr repository delete -n MyRegistry --image hello-world@sha256:abc123
"""

helps['acr repository untag'] = """
    type: command
    short-summary: Untag an image in a container registry.
    long-summary: This command does not delete the manifest referenced by the tag or any associated layer data.
    examples:
        - name: Untag an image from a repository.
          text:
            az acr repository untag -n MyRegistry --image hello-world:latest
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
        - name: Create a webhook for a container registry that will deliver docker push and delete events to a service URI.
          text: >
            az acr webhook create -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push delete
        - name: Create a webhook for a container registry that will deliver docker push events to a service URI with a basic authentication header.
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

helps['acr build-task create'] = """
    type: command
    short-summary: Creates a new build definition which can be triggered by git commits or base image updates.
    examples:
        - name: Create a build definition which updates on git commits and base image updates.
          text: >
            az acr build-task create -t helloworld:{{.Build.ID}} -n helloworld -r myRegistry -c https://github.com/Azure-Samples/acr-build-helloworld-node --git-access-token 0000000000000000000000000000000000000000
"""

helps['acr build-task show'] = """
    type: command
    short-summary: Get the properties of a specified build task.
    examples:
        - name: Get the details of a build task, displaying the results in a table.
          text: >
            az acr build-task show -n MyBuildTask -r MyRegistry -o table

        - name: Get the details of a build task including secure properties.
          text: >
            az acr build-task show -n MyBuildTask -r MyRegistry --with-secure-properties
"""

helps['acr build-task list'] = """
    type: command
    short-summary: List the build tasks for a container registry.
    examples:
        - name: List build tasks and show the results in a table.
          text: >
            az acr build-task list -r MyRegistry -o table
"""

helps['acr build-task delete'] = """
    type: command
    short-summary: Delete a build task from a container registry.
    examples:
        - name: Delete a build task from a container registry.
          text: >
            az acr build-task delete -n MyBuildTask -r MyRegistry
"""

helps['acr build-task update'] = """
    type: command
    short-summary: Update a build task for a container registry.
    examples:
        - name: Update the git access token for a build definition in a container registry.
          text: >
            az acr build-task update -n MyBuildTask -r MyRegistry --git-access-token 0000000000000000000000000000000000000000
"""

helps['acr build-task list-builds'] = """
    type: command
    short-summary: List all of the executed builds for a registry, with the ability to filter by a specific build task.
    examples:
        - name: List builds for a build task and show the results in a table.
          text: >
            az acr build-task list-builds -n MyBuildTask -r MyRegistry -o table
        - name: List all of the builds for a registry and show the results in a table.
          text: >
            az acr build-task list-builds -r MyRegistry -o table
        - name: List the last 10 successful builds for a registry and show the results in a table.
          text: >
            az acr build-task list-builds -r MyRegistry --build-status Succeeded --top 10 -o table
        - name: List all of the builds that built the image 'hello-world:latest' for a registry and show the results in a table.
          text: >
            az acr build-task list-builds -r MyRegistry --image hello-world:latest -o table
"""

helps['acr build-task show-build'] = """
    type: command
    short-summary: Get the properties of a specified build.
    examples:
        - name:  Get the details of a build, displaying the results in a table.
          text: >
            az acr build-task show-build -n MyBuildTask -r MyRegistry --build-id MyBuild -o table
"""

helps['acr build-task run'] = """
    type: command
    short-summary: Trigger a build task that might otherwise be waiting for git commits or base image update triggers.
    examples:
        - name: Trigger a build task.
          text: >
            az acr build-task run -n MyBuildTask -r MyRegistry
"""

helps['acr build-task update-build'] = """
    type: command
    short-summary: Patch the build properties.
    examples:
        - name: Update an existing build to be archived.
          text: >
            az acr build-task update-build -r MyRegistry --build-id MyBuild --no-archive false
"""

helps['acr build-task logs'] = """
    type: command
    short-summary: Show logs for a particular build. If no build-id is supplied, it shows logs for the last created build.
    examples:
        - name: Show logs for the last created build in the registry.
          text: >
            az acr build-task logs -r MyRegistry
        - name: Show logs for the last created build in the registry, filtered by build task.
          text: >
            az acr build-task logs -r MyRegistry -n MyBuildTask
        - name: Show logs for a particular build.
          text: >
            az acr build-task logs -r MyRegistry --build-id buildId
        - name: Show logs for the last created build in the registry that built the image 'hello-world:latest'.
          text: >
            az acr build-task logs -r MyRegistry --image hello-world:latest
"""

helps['acr build'] = """
    type: command
    short-summary: Queues a quick docker build providing interactive feedback.
    examples:
        - name: Queue a local context, pushed to ACR with streaming logs.
          text: >
            az acr build -t sample/helloworld:{{.Build.ID}} -r MyRegistry .
    examples:
        - name: Queue a local context, pushed to ACR without streaming logs.
          text: >
            az acr build -t sample/helloworld:{{.Build.ID}} -r MyRegistry --no-logs .
    examples:
        - name: Queue a local context, validating the build is successful, without pushing to the registry.
          text: >
            az acr build -r MyRegistry .
"""

helps['acr import'] = """
    type: command
    short-summary: Imports an image to the container registry from source.
    examples:
        - name: Import an image to the target registry and inherits sourcerepository:sourcetag from source.
          text: >
            az acr import -n MyRegistry --source sourceregistry.azurecr.io/sourcerepository:sourcetag
        - name: Import an image from a registry in a different subscription.
          text: >
            az acr import -n MyRegistry --source sourcerepository:sourcetag -t targetrepository:targettag -r /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/sourceResourceGroup/providers/Microsoft.ContainerRegistry/registries/sourceRegistry
"""
