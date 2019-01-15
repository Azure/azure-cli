# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["acr config content-trust show"] = """
"type": |-
    command
"short-summary": |-
    Show the configured content-trust policy for an Azure Container Registry.
"""

helps["acr import"] = """
"type": |-
    command
"short-summary": |-
    Imports an image to an Azure Container Registry from another Container Registry. Import removes the need to docker pull, docker tag, docker push.
"examples":
-   "name": |-
        Imports an image to an Azure Container Registry from another Container Registry. Import removes the need to docker pull, docker tag, docker push.
    "text": |-
        az acr import --source sourceregistry.azurecr.io/sourcerepository:sourcetag --name MyRegistry
"""

helps["acr build"] = """
"type": |-
    command
"short-summary": |-
    Queues a quick build, providing streaming logs for an Azure Container Registry.
"examples":
-   "name": |-
        Queues a quick build, providing streamed logs for an Azure Container Registry.
    "text": |-
        az acr build --registry MyRegistry . --image sample/hello-world:{{.Run.ID}}
"""

helps["acr webhook show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a webhook.
"""

helps["acr build-task run"] = """
"type": |-
    command
"short-summary": |-
    Trigger a build task that might otherwise be waiting for git commits or base image update triggers for an Azure Container Registry.
"""

helps["acr build-task update"] = """
"type": |-
    command
"short-summary": |-
    Update a build task for an Azure Container Registry.
"""

helps["acr config"] = """
"type": |-
    group
"short-summary": |-
    Configure policies for Azure Container Registries.
"""

helps["acr repository show-manifests"] = """
"type": |-
    command
"short-summary": |-
    Show manifests of a repository in an Azure Container Registry.
"""

helps["acr helm repo"] = """
"type": |-
    group
"short-summary": |-
    Manage helm chart repositories for Azure Container Registries.
"""

helps["acr create"] = """
"type": |-
    command
"short-summary": |-
    Creates an Azure Container Registry.
"examples":
-   "name": |-
        Creates an Azure Container Registry.
    "text": |-
        az acr create --name MyRegistry --sku Standard --resource-group MyResourceGroup
"""

helps["acr task show"] = """
"type": |-
    command
"short-summary": |-
    Get the properties of a named task for an Azure Container Registry.
"""

helps["acr helm push"] = """
"type": |-
    command
"short-summary": |-
    Push a helm chart package to an Azure Container Registry.
"""

helps["acr task list-runs"] = """
"type": |-
    command
"short-summary": |-
    List all of the executed runs for an Azure Container Registry, with the ability to filter by a specific Task.
"""

helps["acr login"] = """
"type": |-
    command
"short-summary": |-
    Log in to an Azure Container Registry through the Docker CLI.
"long-summary": |-
    Docker must be installed on your machine.
"examples":
-   "name": |-
        Log in to an Azure Container Registry through the Docker CLI.
    "text": |-
        az acr login --name MyRegistry
"""

helps["acr build-task create"] = """
"type": |-
    command
"short-summary": |-
    Creates a new build definition which can be triggered by git commits or base image updates for an Azure Container Registry.
"""

helps["acr repository untag"] = """
"type": |-
    command
"short-summary": |-
    Untag an image in an Azure Container Registry.
"long-summary": |-
    This command does not delete the manifest referenced by the tag or any associated layer data.
"examples":
-   "name": |-
        Untag an image in an Azure Container Registry.
    "text": |-
        az acr repository untag --image hello-world:latest --name MyRegistry
"""

helps["acr repository list"] = """
"type": |-
    command
"short-summary": |-
    List repositories in an Azure Container Registry.
"examples":
-   "name": |-
        List repositories in an Azure Container Registry.
    "text": |-
        az acr repository list --output json --name MyRegistry
"""

helps["acr repository update"] = """
"type": |-
    command
"short-summary": |-
    Update the attributes of a repository or image in an Azure Container Registry.
"""

helps["acr webhook delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a webhook from an Azure Container Registry.
"""

helps["acr replication show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a replicated region.
"""

helps["acr webhook"] = """
"type": |-
    group
"short-summary": |-
    Manage webhooks for Azure Container Registries.
"""

helps["acr helm show"] = """
"type": |-
    command
"short-summary": |-
    Describe a helm chart in an Azure Container Registry.
"""

helps["acr task logs"] = """
"type": |-
    command
"short-summary": |-
    Show logs for a particular run. If no run-id is supplied, show logs for the last created run.
"""

helps["acr task update-run"] = """
"type": |-
    command
"short-summary": |-
    Patch the run properties of an Azure Container Registry Task.
"""

helps["acr config content-trust"] = """
"type": |-
    group
"short-summary": |-
    Manage content-trust policy for Azure Container Registries.
"""

helps["acr replication create"] = """
"type": |-
    command
"short-summary": |-
    Create a replicated region for an Azure Container Registry.
"""

helps["acr helm"] = """
"type": |-
    group
"short-summary": |-
    Manage helm charts for Azure Container Registries.
"""

helps["acr credential show"] = """
"type": |-
    command
"short-summary": |-
    Get the login credentials for an Azure Container Registry.
"examples":
-   "name": |-
        Get the login credentials for an Azure Container Registry.
    "text": |-
        az acr credential show --name MyRegistry
"""

helps["acr"] = """
"type": |-
    group
"short-summary": |-
    Manage private registries with Azure Container Registries.
"""

helps["acr webhook list-events"] = """
"type": |-
    command
"short-summary": |-
    List recent events for a webhook.
"""

helps["acr task update"] = """
"type": |-
    command
"short-summary": |-
    Update a task for an Azure Container Registry.
"""

helps["acr build-task"] = """
"type": |-
    group
"short-summary": |-
    Manage build definitions, which can be triggered by git commits or base image updates for OS & Framework Patching.
"""

helps["acr build-task update-build"] = """
"type": |-
    command
"short-summary": |-
    Patch the build properties of an Azure Container Registry.
"""

helps["acr show-usage"] = """
"type": |-
    command
"short-summary": |-
    Get the storage usage for an Azure Container Registry.
"""

helps["acr build-task delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a build task from an Azure Container Registry.
"""

helps["acr run"] = """
"type": |-
    command
"short-summary": |-
    Queues a quick run providing streamed logs for an Azure Container Registry.
"""

helps["acr replication list"] = """
"type": |-
    command
"short-summary": |-
    List all of the regions for a geo-replicated Azure Container Registry.
"""

helps["acr build-task logs"] = """
"type": |-
    command
"short-summary": |-
    Show logs for a particular build. If no build-id is supplied, display the logs for the last created build.
"""

helps["acr task show-run"] = """
"type": |-
    command
"short-summary": |-
    Get the properties of a specified run of an Azure Container Registry Task.
"""

helps["acr webhook update"] = """
"type": |-
    command
"short-summary": |-
    Update a webhook.
"""

helps["acr list"] = """
"type": |-
    command
"short-summary": |-
    Lists all the container registries under the current subscription.
"examples":
-   "name": |-
        Lists all the container registries under the current subscription.
    "text": |-
        az acr list --output json --query [0] --resource-group MyResourceGroup
"""

helps["acr show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an Azure Container Registry.
"examples":
-   "name": |-
        Get the details of an Azure Container Registry.
    "text": |-
        az acr show --output json --query [0] --name MyRegistry
"""

helps["acr task"] = """
"type": |-
    group
"short-summary": |-
    Manage a collection of steps for building, testing and OS & Framework patching container images using Azure Container Registries.
"""

helps["acr config content-trust update"] = """
"type": |-
    command
"short-summary": |-
    Update content-trust policy for an Azure Container Registry.
"""

helps["acr task cancel-run"] = """
"type": |-
    command
"short-summary": |-
    Cancel a specified run of an Azure Container Registry.
"""

helps["acr credential renew"] = """
"type": |-
    command
"short-summary": |-
    Regenerate login credentials for an Azure Container Registry.
"""

helps["acr credential"] = """
"type": |-
    group
"short-summary": |-
    Manage login credentials for Azure Container Registries.
"""

helps["acr repository show-tags"] = """
"type": |-
    command
"short-summary": |-
    Show tags for a repository in an Azure Container Registry.
"""

helps["acr webhook get-config"] = """
"type": |-
    command
"short-summary": |-
    Get the service URI and custom headers for the webhook.
"""

helps["acr task delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a task from an Azure Container Registry.
"""

helps["acr repository delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a repository or image in an Azure Container Registry.
"long-summary": |-
    This command deletes all associated layer data that are not referenced by any other manifest in the container registry.
"examples":
-   "name": |-
        Delete a repository or image in an Azure Container Registry.
    "text": |-
        az acr repository delete --yes  --image hello-world:latest --name MyRegistry
"""

helps["acr build-task list"] = """
"type": |-
    command
"short-summary": |-
    List the build tasks for an Azure Container Registry.
"""

helps["acr webhook create"] = """
"type": |-
    command
"short-summary": |-
    Create a webhook for an Azure Container Registry.
"""

helps["acr replication"] = """
"type": |-
    group
"short-summary": |-
    Manage geo-replicated regions of Azure Container Registries.
"""

helps["acr repository show"] = """
"type": |-
    command
"short-summary": |-
    Get the attributes of a repository or image in an Azure Container Registry.
"examples":
-   "name": |-
        Get the attributes of a repository or image in an Azure Container Registry.
    "text": |-
        az acr repository show --image hello-world:latest --name MyRegistry
-   "name": |-
        Show tags for a repository in an Azure Container Registry.
    "text": |-
        az acr repository show-tags --output json --repository MyRepository --name MyRegistry
-   "name": |-
        Show manifests of a repository in an Azure Container Registry.
    "text": |-
        az acr repository show-manifests --repository MyRepository --name MyRegistry
"""

helps["acr replication delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a replicated region from an Azure Container Registry.
"""

helps["acr check-name"] = """
"type": |-
    command
"short-summary": |-
    Checks if an Azure Container Registry name is valid and available for use.
"""

helps["acr task list"] = """
"type": |-
    command
"short-summary": |-
    List the tasks for an Azure Container Registry.
"examples":
-   "name": |-
        List all of the executed runs for an Azure Container Registry, with the ability to filter by a specific Task.
    "text": |-
        az acr task list-runs --registry MyRegistry --output json
"""

helps["acr helm delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a helm chart version in an Azure Container Registry.
"""

helps["acr build-task show"] = """
"type": |-
    command
"short-summary": |-
    Get the properties of a specified build task for an Azure Container Registry.
"""

helps["acr build-task show-build"] = """
"type": |-
    command
"short-summary": |-
    Get the properties of a specified build for an Azure Container Registry.
"""

helps["acr webhook list"] = """
"type": |-
    command
"short-summary": |-
    List all of the webhooks for an Azure Container Registry.
"""

helps["acr helm list"] = """
"type": |-
    command
"short-summary": |-
    List all helm charts in an Azure Container Registry.
"""

helps["acr delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes an Azure Container Registry.
"""

helps["acr webhook ping"] = """
"type": |-
    command
"short-summary": |-
    Trigger a ping event for a webhook.
"""

helps["acr task create"] = """
"type": |-
    command
"short-summary": |-
    Creates a series of steps for building, testing and OS & Framework patching containers. Tasks support triggers from git commits and base image updates.
"""

helps["acr task run"] = """
"type": |-
    command
"short-summary": |-
    Manually trigger a task that might otherwise be waiting for git commits or base image update triggers.
"examples":
-   "name": |-
        Manually trigger a task that might otherwise be waiting for git commits or base image update triggers.
    "text": |-
        az acr task run --registry MyRegistry --name MyTask
"""

helps["acr update"] = """
"type": |-
    command
"short-summary": |-
    Update an Azure Container Registry.
"examples":
-   "name": |-
        Update an Azure Container Registry.
    "text": |-
        az acr update --admin-enabled true --name MyRegistry
"""

helps["acr build-task list-builds"] = """
"type": |-
    command
"short-summary": |-
    List all of the executed builds for an Azure Container Registry.
"""

helps["acr replication update"] = """
"type": |-
    command
"short-summary": |-
    Updates a replication.
"""

helps["acr repository"] = """
"type": |-
    group
"short-summary": |-
    Manage repositories (image names) for Azure Container Registries.
"""

helps["acr helm repo add"] = """
"type": |-
    command
"short-summary": |-
    Add a helm chart repository from an Azure Container Registry through the Helm CLI.
"long-summary": |-
    Helm must be installed on your machine.
"""

