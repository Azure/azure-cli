# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps
# pylint: disable=line-too-long, too-many-lines

helps['acr'] = """
type: group
short-summary: Manage private registries with Azure Container Registries.
"""

helps['acr build'] = """
type: command
short-summary: Queues a quick build, providing streaming logs for an Azure Container Registry.
examples:
  - name: Queue a local context as a Linux build, tag it, and push it to the registry.
    text: >
        az acr build -t sample/hello-world:{{.Run.ID}} -r MyRegistry .
  - name: Queue a local context as a Linux build, tag it, and push it to the registry without streaming logs.
    text: >
        az acr build -t sample/hello-world:{{.Run.ID}} -r MyRegistry --no-logs .
  - name: Queue a local context as a Linux build without pushing it to the registry.
    text: >
        az acr build -t sample/hello-world:{{.Run.ID}} -r MyRegistry --no-push .
  - name: Queue a local context as a Linux build without pushing it to the registry.
    text: >
        az acr build -r MyRegistry .
  - name: Queue a remote GitHub context as a Windows build and x86 architecture, tag it, and push it to the registry.
    text: >
        az acr build -r MyRegistry https://github.com/Azure/acr-builder.git -f Windows.Dockerfile --platform Windows/x86
  - name: Queue a local context as a Linux build on arm/v7 architecture, tag it, and push it to the registry.
    text: >
        az acr build -t sample/hello-world:{{.Run.ID}} -r MyRegistry . --platform linux/arm/v7
"""

helps['acr check-name'] = """
type: command
short-summary: Checks if an Azure Container Registry name is valid and available for use.
examples:
  - name: Check if a registry name already exists.
    text: >
        az acr check-name -n doesthisnameexist
"""

helps['acr config'] = """
type: group
short-summary: Configure policies for Azure Container Registries.
"""

helps['acr config content-trust'] = """
type: group
short-summary: Manage content-trust policy for Azure Container Registries.
"""

helps['acr config content-trust show'] = """
type: command
short-summary: Show the configured content-trust policy for an Azure Container Registry.
examples:
  - name: Show the configured content-trust policy for an Azure Container Registry
    text: >
        az acr config content-trust show -n MyRegistry
"""

helps['acr config content-trust update'] = """
type: command
short-summary: Update content-trust policy for an Azure Container Registry.
examples:
  - name: Update content-trust policy for an Azure Container Registry
    text: >
        az acr config content-trust update -n MyRegistry --status Enabled
"""

helps['acr create'] = """
type: command
short-summary: Creates an Azure Container Registry.
examples:
  - name: Create a managed container registry with the Standard SKU.
    text: >
        az acr create -n MyRegistry -g MyResourceGroup --sku Standard
  - name: Create an Azure Container Registry with a new storage account with the Classic SKU (Classic registries are being deprecated by March 2019).
    text: >
        az acr create -n MyRegistry -g MyResourceGroup --sku Classic
"""

helps['acr credential'] = """
type: group
short-summary: Manage login credentials for Azure Container Registries.
"""

helps['acr credential renew'] = """
type: command
short-summary: Regenerate login credentials for an Azure Container Registry.
examples:
  - name: Renew the second password for an Azure Container Registry.
    text: >
        az acr credential renew -n MyRegistry --password-name password2
"""

helps['acr credential show'] = """
type: command
short-summary: Get the login credentials for an Azure Container Registry.
examples:
  - name: Get the login credentials for an Azure Container Registry.
    text: >
        az acr credential show -n MyRegistry
  - name: Get the username used to log in to an Azure Container Registry.
    text: >
        az acr credential show -n MyRegistry --query username
  - name: Get a password used to log in to an Azure Container Registry.
    text: >
        az acr credential show -n MyRegistry --query passwords[0].value
"""

helps['acr delete'] = """
type: command
short-summary: Deletes an Azure Container Registry.
examples:
  - name: Delete an Azure Container Registry.
    text: >
        az acr delete -n MyRegistry
"""

helps['acr helm'] = """
type: group
short-summary: Manage helm charts for Azure Container Registries.
"""

helps['acr helm delete'] = """
type: command
short-summary: Delete a helm chart version in an Azure Container Registry.
examples:
  - name: Delete all versions of a helm chart in an Azure Container Registry
    text: >
        az acr helm delete -n MyRegistry mychart
  - name: Delete a helm chart version in an Azure Container Registry
    text: >
        az acr helm delete -n MyRegistry mychart --version 0.3.2
"""

helps['acr helm list'] = """
type: command
short-summary: List all helm charts in an Azure Container Registry.
examples:
  - name: List all helm charts in an Azure Container Registry
    text: >
        az acr helm list -n MyRegistry
"""

helps['acr helm push'] = """
type: command
short-summary: Push a helm chart package to an Azure Container Registry.
examples:
  - name: Push a chart package to an Azure Container Registry
    text: >
        az acr helm push -n MyRegistry mychart-0.3.2.tgz
  - name: Push a chart package to an Azure Container Registry, overwriting the existing one.
    text: >
        az acr helm push -n MyRegistry mychart-0.3.2.tgz --force
"""

helps['acr helm repo'] = """
type: group
short-summary: Manage helm chart repositories for Azure Container Registries.
"""

helps['acr helm repo add'] = """
type: command
short-summary: Add a helm chart repository from an Azure Container Registry through the Helm CLI.
long-summary: Helm must be installed on your machine.
examples:
  - name: Add a helm chart repository from an Azure Container Registry to manage helm charts.
    text: >
        az acr helm repo add -n MyRegistry
"""

helps['acr helm show'] = """
type: command
short-summary: Describe a helm chart in an Azure Container Registry.
examples:
  - name: Show all versions of a helm chart in an Azure Container Registry
    text: >
        az acr helm show -n MyRegistry mychart
  - name: Show a helm chart version in an Azure Container Registry
    text: >
        az acr helm show -n MyRegistry mychart --version 0.3.2
"""

helps['acr import'] = """
type: command
short-summary: Imports an image to an Azure Container Registry from another Container Registry. Import removes the need to docker pull, docker tag, docker push.
examples:
  - name: Import an image to the target registry and inherits sourcerepository:sourcetag from the source registry.
    text: >
        az acr import -n MyRegistry --source sourceregistry.azurecr.io/sourcerepository:sourcetag
  - name: Import an image from a registry in a different subscription.
    text: >
        az acr import -n MyRegistry --source sourcerepository:sourcetag -t targetrepository:targettag -r /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/sourceResourceGroup/providers/Microsoft.ContainerRegistry/registries/sourceRegistry
  - name: Import an image from a public repository in Docker Hub
    text: >
        az acr import -n MyRegistry --source docker.io/sourcerepository:sourcetag -t targetrepository:targettag
"""

helps['acr list'] = """
type: command
short-summary: Lists all the container registries under the current subscription.
examples:
  - name: List container registries and show the results in a table, across multiple resource groups.
    text: >
        az acr list -o table
  - name: List container registries in a resource group and show the results in a table.
    text: >
        az acr list -g MyResourceGroup -o table
"""

helps['acr login'] = """
type: command
short-summary: Log in to an Azure Container Registry through the Docker CLI.
long-summary: Docker must be installed on your machine.
examples:
  - name: Log in to an Azure Container Registry
    text: >
        az acr login -n MyRegistry
"""

helps['acr network-rule'] = """
type: group
short-summary: Manage network rules for Azure Container Registries.
"""

helps['acr network-rule add'] = """
type: command
short-summary: Add a network rule.
examples:
  - name: Add a rule to allow access for a subnet in the same resource group as the registry.
    text: >
        az acr network-rule add -n MyRegistry --vnet-name myvnet --subnet mysubnet
  - name: Add a rule to allow access for a subnet in a different subscription or resource group.
    text: >
        az acr network-rule add -n MyRegistry --subnet /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myRG/providers/Microsoft.Network/virtualNetworks/myvnet/subnets/mysubnet
  - name: Add a rule to allow access for a specific IP address-range.
    text: >
        az acr network-rule add -n MyRegistry --ip-address 23.45.1.0/24
"""

helps['acr network-rule list'] = """
type: command
short-summary: List network rules.
examples:
  - name: List network rules for a registry.
    text: >
        az acr network-rule list -n MyRegistry
"""

helps['acr network-rule remove'] = """
type: command
short-summary: Remove a network rule.
examples:
  - name: Remove a rule that allows access for a subnet in the same resource group as the registry.
    text: >
        az acr network-rule remove -n MyRegistry --vnet-name myvnet --subnet mysubnet
  - name: Remove a rule that allows access for a subnet in a different subscription or resource group.
    text: >
        az acr network-rule remove -n MyRegistry --subnet /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myRG/providers/Microsoft.Network/virtualNetworks/myvnet/subnets/mysubnet
  - name: Remove a rule that allows access for a specific IP address-range.
    text: >
        az acr network-rule remove -n MyRegistry --ip-address 23.45.1.0/24
"""

helps['acr replication'] = """
type: group
short-summary: Manage geo-replicated regions of Azure Container Registries.
"""

helps['acr replication create'] = """
type: command
short-summary: Create a replicated region for an Azure Container Registry.
examples:
  - name: Create a replicated region for an Azure Container Registry.
    text: >
        az acr replication create -r MyRegistry -l westus
"""

helps['acr replication delete'] = """
type: command
short-summary: Delete a replicated region from an Azure Container Registry.
examples:
  - name: Delete a replicated region from an Azure Container Registry.
    text: >
        az acr replication delete -n MyReplication -r MyRegistry
"""

helps['acr replication list'] = """
type: command
short-summary: List all of the regions for a geo-replicated Azure Container Registry.
examples:
  - name: List replications and show the results in a table.
    text: >
        az acr replication list -r MyRegistry -o table
"""

helps['acr replication show'] = """
type: command
short-summary: Get the details of a replicated region.
examples:
  - name: Get the details of a replicated region
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

helps['acr repository'] = """
type: group
short-summary: Manage repositories (image names) for Azure Container Registries.
"""

helps['acr repository delete'] = """
type: command
short-summary: Delete a repository or image in an Azure Container Registry.
long-summary: This command deletes all associated layer data that are not referenced by any other manifest in the container registry.
examples:
  - name: Delete a repository from an Azure Container Registry. This deletes all manifests and tags under 'hello-world'.
    text: az acr repository delete -n MyRegistry --repository hello-world
  - name: Delete an image by tag. This deletes the manifest referenced by 'hello-world:latest' and all other tags referencing the manifest.
    text: az acr repository delete -n MyRegistry --image hello-world:latest
  - name: Delete an image by sha256-based manifest digest. This deletes the manifest identified by 'hello-world@sha256:abc123' and all tags referencing the manifest.
    text: az acr repository delete -n MyRegistry --image hello-world@sha256:abc123
"""

helps['acr repository list'] = """
type: command
short-summary: List repositories in an Azure Container Registry.
examples:
  - name: List repositories in a given Azure Container Registry.
    text: az acr repository list -n MyRegistry
"""

helps['acr repository show'] = """
type: command
short-summary: Get the attributes of a repository or image in an Azure Container Registry.
examples:
  - name: Get the attributes of the repository 'hello-world'.
    text: az acr repository show -n MyRegistry --repository hello-world
  - name: Get the attributes of the image referenced by tag 'hello-world:latest'.
    text: az acr repository show -n MyRegistry --image hello-world:latest
  - name: Get the attributes of the image referenced by digest 'hello-world@sha256:abc123'.
    text: az acr repository show -n MyRegistry --image hello-world@sha256:abc123
"""

helps['acr repository show-manifests'] = """
type: command
short-summary: Show manifests of a repository in an Azure Container Registry.
examples:
  - name: Show manifests of a repository in an Azure Container Registry.
    text: az acr repository show-manifests -n MyRegistry --repository MyRepository
  - name: Show the latest 10 manifests ordered by timestamp of a repository in an Azure Container Registry.
    text: az acr repository show-manifests -n MyRegistry --repository MyRepository --top 10 --orderby time_desc
  - name: Show the detailed information of the latest 10 manifests ordered by timestamp of a repository in an Azure Container Registry.
    text: az acr repository show-manifests -n MyRegistry --repository MyRepository --top 10 --orderby time_desc --detail
"""

helps['acr repository show-tags'] = """
type: command
short-summary: Show tags for a repository in an Azure Container Registry.
examples:
  - name: Show tags of a repository in an Azure Container Registry.
    text: az acr repository show-tags -n MyRegistry --repository MyRepository
  - name: Show the detailed information of tags of a repository in an Azure Container Registry.
    text: az acr repository show-tags -n MyRegistry --repository MyRepository --detail
  - name: Show the detailed information of the latest 10 tags ordered by timestamp of a repository in an Azure Container Registry.
    text: az acr repository show-tags -n MyRegistry --repository MyRepository --top 10 --orderby time_desc --detail
"""

helps['acr repository untag'] = """
type: command
short-summary: Untag an image in an Azure Container Registry.
long-summary: This command does not delete the manifest referenced by the tag or any associated layer data.
examples:
  - name: Untag an image from a repository.
    text: az acr repository untag -n MyRegistry --image hello-world:latest
"""

helps['acr repository update'] = """
type: command
short-summary: Update the attributes of a repository or image in an Azure Container Registry.
examples:
  - name: Update the attributes of the repository 'hello-world' to disable write operation.
    text: az acr repository update -n MyRegistry --repository hello-world --write-enabled false
  - name: Update the attributes of the image referenced by tag 'hello-world:latest' to disable write operation.
    text: az acr repository update -n MyRegistry --image hello-world:latest --write-enabled false
  - name: Update the attributes of the image referenced by digest 'hello-world@sha256:abc123' to disable write operation.
    text: az acr repository update -n MyRegistry --image hello-world@sha256:abc123 --write-enabled false
"""

helps['acr run'] = """
type: command
short-summary: Queues a quick run providing streamed logs for an Azure Container Registry.
examples:
  - name: Queue a local context, pushed to ACR with streaming logs.
    text: >
        az acr run -r MyRegistry -f bash-echo.yaml .
  - name: Queue a remote git context with streaming logs.
    text: >
        az acr run -r MyRegistry https://github.com/Azure-Samples/acr-tasks.git -f hello-world.yaml
  - name: Queue a remote git context with streaming logs and runs the task on Linux platform.
    text: >
        az acr run -r MyRegistry https://github.com/Azure-Samples/acr-tasks.git -f build-hello-world.yaml --platform linux
"""

helps['acr show'] = """
type: command
short-summary: Get the details of an Azure Container Registry.
examples:
  - name: Get the login server for an Azure Container Registry.
    text: >
        az acr show -n MyRegistry --query loginServer
"""

helps['acr show-usage'] = """
type: command
short-summary: Get the storage usage for an Azure Container Registry.
examples:
  - name: Get the storage usage for an Azure Container Registry.
    text: >
        az acr show-usage -n MyRegistry
"""

helps['acr task'] = """
type: group
short-summary: Manage a collection of steps for building, testing and OS & Framework patching container images using Azure Container Registries.
"""

helps['acr task cancel-run'] = """
type: command
short-summary: Cancel a specified run of an Azure Container Registry.
examples:
  - name: Cancel a run
    text: >
        az acr task cancel-run -r MyRegistry --run-id runId
"""

helps['acr task create'] = """
type: command
short-summary: Creates a series of steps for building, testing and OS & Framework patching containers. Tasks support triggers from git commits and base image updates.
examples:
  - name: Create a Linux task from a public GitHub repository which builds the hello-world image without triggers
    text: >
        az acr task create -t hello-world:{{.Run.ID}} -n hello-world -r MyRegistry -c https://github.com/Azure-Samples/acr-build-helloworld-node.git -f Dockerfile --commit-trigger-enabled false --pull-request-trigger-enabled false
  - name: Create a Linux task using a private GitHub repository which builds the hello-world image without triggers on Arm architecture (V7 variant)
    text: >
        az acr task create -t hello-world:{{.Run.ID}} -n hello-world -r MyRegistry -c https://github.com/Azure-Samples/acr-build-helloworld-node.git -f Dockerfile --commit-trigger-enabled false --pull-request-trigger-enabled false --git-access-token 0000000000000000000000000000000000000000 --platform linux/arm/v7
  - name: Create a Linux task from a public GitHub repository which builds the hello-world image with a git commit trigger
    text: >
        az acr task create -t hello-world:{{.Run.ID}} -n hello-world -r MyRegistry -c https://github.com/Azure-Samples/acr-build-helloworld-node.git -f Dockerfile --git-access-token 0000000000000000000000000000000000000000
  - name: Create a Windows task from a public GitHub repository which builds the Azure Container Builder image on Amd64 architecture.
    text: >
        az acr task create -t acb:{{.Run.ID}} -n acb-win -r MyRegistry -c https://github.com/Azure/acr-builder.git -f Windows.Dockerfile --commit-trigger-enabled false --pull-request-trigger-enabled false --platform Windows/amd64
"""

helps['acr task delete'] = """
type: command
short-summary: Delete a task from an Azure Container Registry.
examples:
  - name: Delete a task from an Azure Container Registry.
    text: >
        az acr task delete -n MyTask -r MyRegistry
"""

helps['acr task list'] = """
type: command
short-summary: List the tasks for an Azure Container Registry.
examples:
  - name: List tasks and show the results in a table.
    text: >
        az acr task list -r MyRegistry -o table
"""

helps['acr task list-runs'] = """
type: command
short-summary: List all of the executed runs for an Azure Container Registry, with the ability to filter by a specific Task.
examples:
  - name: List all of the runs for a registry and show the results in a table.
    text: >
        az acr task list-runs -r MyRegistry -o table
  - name: List runs for a task and show the results in a table.
    text: >
        az acr task list-runs -r MyRegistry -n MyTask -o table
  - name: List the last 10 successful runs for a registry and show the results in a table.
    text: >
        az acr task list-runs -r MyRegistry --run-status Succeeded --top 10 -o table
  - name: List all of the runs that built the image 'hello-world' for a registry and show the results in a table.
    text: >
        az acr task list-runs -r MyRegistry --image hello-world -o table
"""

helps['acr task logs'] = """
type: command
short-summary: Show logs for a particular run. If no run-id is supplied, show logs for the last created run.
examples:
  - name: Show logs for the last created run in the registry.
    text: >
        az acr task logs -r MyRegistry
  - name: Show logs for the last created run in the registry, filtered by task.
    text: >
        az acr task logs -r MyRegistry -n MyTask
  - name: Show logs for a particular run.
    text: >
        az acr task logs -r MyRegistry --run-id runId
  - name: Show logs for the last created run in the registry that built the image 'hello-world'.
    text: >
        az acr task logs -r MyRegistry --image hello-world
"""

helps['acr task run'] = """
type: command
short-summary: Manually trigger a task that might otherwise be waiting for git commits or base image update triggers.
examples:
  - name: Trigger a task.
    text: >
        az acr task run -n MyTask -r MyRegistry
"""

helps['acr task show'] = """
type: command
short-summary: Get the properties of a named task for an Azure Container Registry.
examples:
  - name: Get the properties of a task, displaying the results in a table.
    text: >
        az acr task show -n MyTask -r MyRegistry -o table

  - name: Get the properties of a task, including secure properties.
    text: >
        az acr task show -n MyTask -r MyRegistry --with-secure-properties
"""

helps['acr task show-run'] = """
type: command
short-summary: Get the properties of a specified run of an Azure Container Registry Task.
examples:
  - name: Get the details of a run, displaying the results in a table.
    text: >
        az acr task show-run -r MyRegistry --run-id runId -o table
"""

helps['acr task update'] = """
type: command
short-summary: Update a task for an Azure Container Registry.
examples:
  - name: Update base image updates to trigger on all dependent images of a multi-stage dockerfile, and status of a task in an Azure Container Registry.
    text: >
        az acr task update -n MyTask -r MyRegistry --base-image-trigger-type All --status Disabled
  - name: Update platform for the Build step of your Task to Windows (prev Linux).
    text: >
        az acr task update -n MyTask -r MyRegistry --platform Windows
"""

helps['acr task update-run'] = """
type: command
short-summary: Patch the run properties of an Azure Container Registry Task.
examples:
  - name: Update an existing run to be archived.
    text: >
        az acr task update-run -r MyRegistry --run-id runId --no-archive false
"""

helps['acr update'] = """
type: command
short-summary: Update an Azure Container Registry.
examples:
  - name: Update tags for an Azure Container Registry.
    text: >
        az acr update -n MyRegistry --tags key1=value1 key2=value2
  - name: Update the storage account for an Azure Container Registry (Classic Registries are being deprecated as of March 2019).
    text: >
        az acr update -n MyRegistry --storage-account-name MyStorageAccount
  - name: Enable the administrator user account for an Azure Container Registry.
    text: >
        az acr update -n MyRegistry --admin-enabled true
"""

helps['acr webhook'] = """
type: group
short-summary: Manage webhooks for Azure Container Registries.
"""

helps['acr webhook create'] = """
type: command
short-summary: Create a webhook for an Azure Container Registry.
examples:
  - name: Create a webhook for an Azure Container Registry that will deliver docker push and delete events to a service URI.
    text: >
        az acr webhook create -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push delete
  - name: Create a webhook for an Azure Container Registry that will deliver docker push events to a service URI with a basic authentication header.
    text: >
        az acr webhook create -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push --headers "Authorization=Basic 000000"
  - name: Create a webhook for an Azure Container Registry that will deliver helm chart push and delete events to a service URI.
    text: >
        az acr webhook create -n MyWebhook -r MyRegistry --uri http://myservice.com --actions chart_push chart_delete
"""

helps['acr webhook delete'] = """
type: command
short-summary: Delete a webhook from an Azure Container Registry.
examples:
  - name: Delete a webhook from an Azure Container Registry.
    text: >
        az acr webhook delete -n MyWebhook -r MyRegistry
"""

helps['acr webhook get-config'] = """
type: command
short-summary: Get the service URI and custom headers for the webhook.
examples:
  - name: Get the configuration information for a webhook.
    text: >
        az acr webhook get-config -n MyWebhook -r MyRegistry
"""

helps['acr webhook list'] = """
type: command
short-summary: List all of the webhooks for an Azure Container Registry.
examples:
  - name: List webhooks and show the results in a table.
    text: >
        az acr webhook list -r MyRegistry -o table
"""

helps['acr webhook list-events'] = """
type: command
short-summary: List recent events for a webhook.
examples:
  - name: List recent events for a webhook.
    text: >
        az acr webhook list-events -n MyWebhook -r MyRegistry
"""

helps['acr webhook ping'] = """
type: command
short-summary: Trigger a ping event for a webhook.
examples:
  - name: Trigger a ping event for a webhook.
    text: >
        az acr webhook ping -n MyWebhook -r MyRegistry
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
