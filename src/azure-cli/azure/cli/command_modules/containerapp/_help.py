# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import

helps['containerapp'] = """
    type: group
    short-summary: Manage Azure Container Apps.
"""

helps['containerapp create'] = """
    type: command
    short-summary: Create a container app.
    examples:
    - name: Create a container app and retrieve its fully qualified domain name.
      text: |
          az containerapp create -n my-containerapp -g MyResourceGroup \\
              --image myregistry.azurecr.io/my-app:v1.0 --environment MyContainerappEnv \\
              --ingress external --target-port 80 \\
              --registry-server myregistry.azurecr.io --registry-username myregistry --registry-password $REGISTRY_PASSWORD \\
              --query properties.configuration.ingress.fqdn
    - name: Create a container app with resource requirements and replica count limits.
      text: |
          az containerapp create -n my-containerapp -g MyResourceGroup \\
              --image nginx --environment MyContainerappEnv \\
              --cpu 0.5 --memory 1.0Gi \\
              --min-replicas 4 --max-replicas 8
    - name: Create a container app with secrets and environment variables.
      text: |
          az containerapp create -n my-containerapp -g MyResourceGroup \\
              --image my-app:v1.0 --environment MyContainerappEnv \\
              --secrets mysecret=secretvalue1 anothersecret="secret value 2" \\
              --env-vars GREETING="Hello, world" SECRETENV=secretref:anothersecret
    - name: Create a container app using a YAML configuration. Example YAML configuration - https://aka.ms/azure-container-apps-yaml
      text: |
          az containerapp create -n my-containerapp -g MyResourceGroup \\
              --environment MyContainerappEnv \\
              --yaml "path/to/yaml/file.yml"
    - name: Create a container app with an http scale rule
      text: |
          az containerapp create -n myapp -g mygroup --environment myenv --image nginx \\
              --scale-rule-name my-http-rule \\
              --scale-rule-http-concurrency 50
    - name: Create a container app with a custom scale rule
      text: |
          az containerapp create -n my-containerapp -g MyResourceGroup \\
              --image my-queue-processor --environment MyContainerappEnv \\
              --min-replicas 4 --max-replicas 8 \\
              --scale-rule-name queue-based-autoscaling \\
              --scale-rule-type azure-queue \\
              --scale-rule-metadata "accountName=mystorageaccountname" \\
                                    "cloud=AzurePublicCloud" \\
                                    "queueLength=5" "queueName=foo" \\
              --scale-rule-auth "connection=my-connection-string-secret-name"
    - name: Create a container app with secrets and mounts them in a volume.
      text: |
          az containerapp create -n my-containerapp -g MyResourceGroup \\
              --image my-app:v1.0 --environment MyContainerappEnv \\
              --secrets mysecret=secretvalue1 anothersecret="secret value 2" \\
              --secret-volume-mount "mnt/secrets"
"""

helps['containerapp update'] = """
    type: command
    short-summary: Update a container app. In multiple revisions mode, create a new revision based on the latest revision.
    examples:
    - name: Update a container app's container image.
      text: |
          az containerapp update -n my-containerapp -g MyResourceGroup \\
              --image myregistry.azurecr.io/my-app:v2.0
    - name: Update a container app's resource requirements and scale limits.
      text: |
          az containerapp update -n my-containerapp -g MyResourceGroup \\
              --cpu 0.5 --memory 1.0Gi \\
              --min-replicas 4 --max-replicas 8
    - name: Update a container app with an http scale rule
      text: |
          az containerapp update -n myapp -g mygroup \\
              --scale-rule-name my-http-rule \\
              --scale-rule-http-concurrency 50
    - name: Update a container app with a custom scale rule
      text: |
          az containerapp update -n myapp -g mygroup \\
              --scale-rule-name my-custom-rule \\
              --scale-rule-type my-custom-type \\
              --scale-rule-metadata key=value key2=value2 \\
              --scale-rule-auth triggerparam=secretref triggerparam=secretref
"""

helps['containerapp delete'] = """
    type: command
    short-summary: Delete a container app.
    examples:
    - name: Delete a container app.
      text: az containerapp delete -g MyResourceGroup -n MyContainerapp
"""

helps['containerapp show'] = """
    type: command
    short-summary: Show details of a container app.
    examples:
    - name: Show the details of a container app.
      text: |
          az containerapp show -n my-containerapp -g MyResourceGroup
"""

helps['containerapp list'] = """
    type: command
    short-summary: List container apps.
    examples:
    - name: List container apps in the current subscription.
      text: |
          az containerapp list
    - name: List container apps by resource group.
      text: |
          az containerapp list -g MyResourceGroup
"""

helps['containerapp list-usages'] = """
    type: command
    short-summary: List usages of subscription level quotas in specific region.
    examples:
    - name: List usages of  quotas in specific region.
      text: |
          az containerapp list-usages -l eastus
"""

helps['containerapp env list-usages'] = """
    type: command
    short-summary: List usages of quotas for specific managed environment.
    examples:
    - name: List usages of quotas for specific managed environment.
      text: |
          az containerapp env list-usages -n MyEnv -g MyResourceGroup
"""

helps['containerapp exec'] = """
    type: command
    short-summary: Open an SSH-like interactive shell within a container app replica
    examples:
    - name: exec into a container app
      text: |
          az containerapp exec -n my-containerapp -g MyResourceGroup
    - name: exec into a particular container app replica and revision
      text: |
          az containerapp exec -n my-containerapp -g MyResourceGroup --replica MyReplica --revision MyRevision
    - name: open a bash shell in a containerapp
      text: |
          az containerapp exec -n my-containerapp -g MyResourceGroup --command bash
"""

helps['containerapp browse'] = """
    type: command
    short-summary: Open a containerapp in the browser, if possible
    examples:
    - name: open a containerapp in the browser
      text: |
          az containerapp browse -n my-containerapp -g MyResourceGroup
"""

helps['containerapp up'] = """
    type: command
    short-summary: Create or update a container app as well as any associated resources (ACR, resource group, container apps environment, GitHub Actions, etc.)
    examples:
    - name: Create a container app from a dockerfile in a GitHub repo (setting up github actions)
      text: |
          az containerapp up -n my-containerapp --repo https://github.com/myAccount/myRepo
    - name: Create a container app from a dockerfile in a local directory (or autogenerate a container if no dockerfile is found)
      text: |
          az containerapp up -n my-containerapp --source .
    - name: Create a container app from an image in a registry
      text: |
          az containerapp up -n my-containerapp --image myregistry.azurecr.io/myImage:myTag
    - name: Create a container app from an image in a registry with ingress enabled and a specified environment
      text: |
          az containerapp up -n my-containerapp --image myregistry.azurecr.io/myImage:myTag --ingress external --target-port 80 --environment MyEnv
"""

helps['containerapp env logs'] = """
    type: group
    short-summary: Show container app environment logs
"""

helps['containerapp env logs show'] = """
    type: command
    short-summary: Show past environment logs and/or print logs in real time (with the --follow parameter)
    examples:
    - name: Fetch the past 20 lines of logs from an app and return
      text: |
          az containerapp env logs show -n MyEnvironment -g MyResourceGroup
    - name: Fetch 30 lines of past logs logs from an environment and print logs as they come in
      text: |
          az containerapp env logs show -n MyEnvironment -g MyResourceGroup --follow --tail 30
"""

helps['containerapp logs'] = """
    type: group
    short-summary: Show container app logs
"""

helps['containerapp logs show'] = """
    type: command
    short-summary: Show past logs and/or print logs in real time (with the --follow parameter). Note that the logs are only taken from one revision, replica, and container (for non-system logs).
    examples:
    - name: Fetch the past 20 lines of logs from an app and return
      text: |
          az containerapp logs show -n my-containerapp -g MyResourceGroup
    - name: Fetch the past 20 lines of system logs from an app and return
      text: |
          az containerapp logs show -n my-containerapp -g MyResourceGroup --type system
    - name: Fetch 30 lines of past logs logs from an app and print logs as they come in
      text: |
          az containerapp logs show -n my-containerapp -g MyResourceGroup --follow --tail 30
    - name: Fetch logs for a particular revision, replica, and container
      text: |
          az containerapp logs show -n my-containerapp -g MyResourceGroup --replica MyReplica --revision MyRevision --container MyContainer
"""

helps['containerapp show-custom-domain-verification-id'] = """
    type: command
    short-summary: Show the verification id for binding app or environment custom domains
    examples:
    - name: Get the verification id, which needs to be added as a TXT record for app custom domain to verify domain ownership
      text: |
          az containerapp show-custom-domain-verification-id
    - name: Get the verification id, which needs to be added as a TXT record for custom environment DNS suffix to verify domain ownership
      text: |
          az containerapp show-custom-domain-verification-id
"""

# Replica Commands
helps['containerapp replica'] = """
    type: group
    short-summary: Manage container app replicas
"""

helps['containerapp replica list'] = """
    type: command
    short-summary: List a container app revision's replica
    examples:
    - name: List a container app's replicas in the latest revision
      text: |
          az containerapp replica list -n my-containerapp -g MyResourceGroup
    - name: List a container app's replicas in a particular revision
      text: |
          az containerapp replica list -n my-containerapp -g MyResourceGroup --revision MyRevision
"""

helps['containerapp replica show'] = """
    type: command
    short-summary: Show a container app replica
    examples:
    - name: Show a replica from the latest revision
      text: |
          az containerapp replica show -n my-containerapp -g MyResourceGroup --replica MyReplica
    - name: Show a replica from the a particular revision
      text: |
          az containerapp replica show -n my-containerapp -g MyResourceGroup --replica MyReplica --revision MyRevision
"""

# Revision Commands
helps['containerapp revision'] = """
    type: group
    short-summary: Commands to manage revisions.
"""

helps['containerapp revision show'] = """
    type: command
    short-summary: Show details of a revision.
    examples:
    - name: Show details of a revision.
      text: |
          az containerapp revision show -n my-containerapp -g MyResourceGroup \\
              --revision MyContainerappRevision
"""

helps['containerapp revision list'] = """
    type: command
    short-summary: List a container app's revisions.
    examples:
    - name: List a container app's revisions.
      text: |
          az containerapp revision list -n my-containerapp -g MyResourceGroup
"""

helps['containerapp revision restart'] = """
    type: command
    short-summary: Restart a revision.
    examples:
    - name: Restart a revision.
      text: |
          az containerapp revision restart -n my-containerapp -g MyResourceGroup --revision MyContainerappRevision
"""

helps['containerapp revision activate'] = """
    type: command
    short-summary: Activate a revision.
    examples:
    - name: Activate a revision.
      text: |
          az containerapp revision activate -g MyResourceGroup --revision MyContainerappRevision
"""

helps['containerapp revision deactivate'] = """
    type: command
    short-summary: Deactivate a revision.
    examples:
    - name: Deactivate a revision.
      text: |
          az containerapp revision deactivate -g MyResourceGroup --revision MyContainerappRevision
"""

helps['containerapp revision set-mode'] = """
    type: command
    short-summary: Set the revision mode of a container app.
    examples:
    - name: Set a container app to single revision mode.
      text: |
          az containerapp revision set-mode -n my-containerapp -g MyResourceGroup --mode Single
"""

helps['containerapp revision copy'] = """
    type: command
    short-summary: Create a revision based on a previous revision.
    examples:
    - name: Create a revision based on the latest revision.
      text: |
          az containerapp revision copy -n my-containerapp -g MyResourceGroup \\
              --cpu 0.75 --memory 1.5Gi
    - name: Create a revision based on a previous revision.
      text: |
          az containerapp revision copy -g MyResourceGroup \\
              --from-revision PreviousRevisionName --cpu 0.75 --memory 1.5Gi

"""

helps['containerapp revision copy'] = """
    type: command
    short-summary: Create a revision based on a previous revision.
    examples:
    - name: Create a revision based on a previous revision.
      text: |
          az containerapp revision copy -n my-containerapp -g MyResourceGroup --cpu 0.75 --memory 1.5Gi
"""

helps['containerapp revision label'] = """
    type: group
    short-summary: Manage revision labels assigned to traffic weights.
"""

helps['containerapp revision label add'] = """
    type: command
    short-summary: Set a revision label to a revision with an associated traffic weight.
    examples:
    - name: Add a label to the latest revision.
      text: |
          az containerapp revision label add -n my-containerapp -g MyResourceGroup --label myLabel --revision latest
    - name: Add a label to a previous revision.
      text: |
          az containerapp revision label add -g MyResourceGroup --label myLabel --revision revisionName
"""

helps['containerapp revision label remove'] = """
    type: command
    short-summary: Remove a revision label from a revision with an associated traffic weight.
    examples:
    - name: Remove a label.
      text: |
          az containerapp revision label remove -n my-containerapp -g MyResourceGroup --label myLabel
"""

helps['containerapp revision label swap'] = """
    type: command
    short-summary: Swap a revision label between two revisions with associated traffic weights.
    examples:
    - name: Swap a revision label between two revisions.
      text: |
          az containerapp revision label swap -n my-containerapp -g MyResourceGroup --source myLabel1 --target myLabel2
"""

# Environment Commands
helps['containerapp env'] = """
    type: group
    short-summary: Commands to manage Container Apps environments.
"""

helps['containerapp env create'] = """
    type: command
    short-summary: Create a Container Apps environment.
    examples:
    - name: Create an environment with an auto-generated Log Analytics workspace.
      text: |
          az containerapp env create -n MyContainerappEnvironment -g MyResourceGroup \\
              --location eastus2
    - name: Create a zone-redundant environment
      text: |
          az containerapp env create -n MyContainerappEnvironment -g MyResourceGroup \\
              --location eastus2 --zone-redundant
    - name: Create an environment with an existing Log Analytics workspace.
      text: |
          az containerapp env create -n MyContainerappEnvironment -g MyResourceGroup \\
              --logs-workspace-id myLogsWorkspaceID \\
              --logs-workspace-key myLogsWorkspaceKey \\
              --location eastus2
    - name: Create an environment with workload profiles enabled.
      text: |
          az containerapp env create -n MyContainerappEnvironment -g MyResourceGroup \\
              --location eastus2 --enable-workload-profiles
    - name: Create an environment without workload profiles enabled.
      text: |
          az containerapp env create -n MyContainerappEnvironment -g MyResourceGroup \\
              --location eastus2 --enable-workload-profiles false
"""


helps['containerapp env update'] = """
    type: command
    short-summary: Update a Container Apps environment.
    examples:
    - name: Update an environment's custom domain configuration.
      text: |
          az containerapp env update -n MyContainerappEnvironment -g MyResourceGroup \\
              --dns-suffix my-suffix.net --certificate-file MyFilePath \\
              --certificate-password MyCertPass
"""


helps['containerapp env delete'] = """
    type: command
    short-summary: Delete a Container Apps environment.
    examples:
    - name: Delete an environment.
      text: az containerapp env delete -n MyContainerappEnvironment -g MyResourceGroup
"""

helps['containerapp env show'] = """
    type: command
    short-summary: Show details of a Container Apps environment.
    examples:
    - name: Show the details of an environment.
      text: |
          az containerapp env show -n MyContainerappEnvironment -g MyResourceGroup
"""

helps['containerapp env list'] = """
    type: command
    short-summary: List Container Apps environments by subscription or resource group.
    examples:
    - name: List environments in the current subscription.
      text: |
          az containerapp env list
    - name: List environments by resource group.
      text: |
          az containerapp env list -g MyResourceGroup
"""

helps['containerapp env dapr-component'] = """
    type: group
    short-summary: Commands to manage Dapr components for the Container Apps environment.
"""

helps['containerapp env dapr-component list'] = """
    type: command
    short-summary: List Dapr components for an environment.
    examples:
    - name: List Dapr components for an environment.
      text: |
          az containerapp env dapr-component list -g MyResourceGroup --name MyEnvironment
"""

helps['containerapp env dapr-component show'] = """
    type: command
    short-summary: Show the details of a Dapr component.
    examples:
    - name: Show the details of a Dapr component.
      text: |
          az containerapp env dapr-component show -g MyResourceGroup --dapr-component-name MyDaprComponentName --name MyEnvironment
"""

helps['containerapp env dapr-component set'] = """
    type: command
    short-summary: Create or update a Dapr component.
    examples:
    - name: Create a Dapr component.
      text: |
          az containerapp env dapr-component set -g MyResourceGroup --name MyEnv --yaml MyYAMLPath --dapr-component-name MyDaprComponentName
"""

helps['containerapp env dapr-component remove'] = """
    type: command
    short-summary: Remove a Dapr component from an environment.
    examples:
    - name: Remove a Dapr component from a Container Apps environment.
      text: |
          az containerapp env dapr-component remove -g MyResourceGroup --dapr-component-name MyDaprComponentName --name MyEnvironment
"""

helps['containerapp env storage'] = """
    type: group
    short-summary: Commands to manage storage for the Container Apps environment.
"""

helps['containerapp env storage list'] = """
    type: command
    short-summary: List the storages for an environment.
    examples:
    - name: List the storages for an environment.
      text: |
          az containerapp env storage list -g MyResourceGroup -n MyEnvironment
"""

helps['containerapp env storage show'] = """
    type: command
    short-summary: Show the details of a storage.
    examples:
    - name: Show the details of a storage.
      text: |
          az containerapp env storage show -g MyResourceGroup --storage-name MyStorageName -n MyEnvironment
"""

helps['containerapp env storage set'] = """
    type: command
    short-summary: Create or update a storage.
    examples:
    - name: Create a storage.
      text: |
          az containerapp env storage set -g MyResourceGroup -n MyEnv --storage-name MyStorageName --access-mode ReadOnly --azure-file-account-key MyAccountKey --azure-file-account-name MyAccountName --azure-file-share-name MyShareName
"""

helps['containerapp env storage remove'] = """
    type: command
    short-summary: Remove a storage from an environment.
    examples:
    - name: Remove a storage from a Container Apps environment.
      text: |
          az containerapp env storage remove -g MyResourceGroup --storage-name MyStorageName -n MyEnvironment
"""

helps['containerapp env workload-profile'] = """
    type: group
    short-summary: Manage the workload profiles of a Container Apps environment
"""

helps['containerapp env workload-profile delete'] = """
    type: command
    short-summary: Delete a workload profile from a Container Apps environment
    examples:
    - name: Delete a workload profile from a Container Apps environment
      text: |
          az containerapp env workload-profile delete -g MyResourceGroup -n MyEnvironment --workload-profile-name my-wlp
"""

helps['containerapp env workload-profile list'] = """
    type: command
    short-summary: List the workload profiles from a Container Apps environment
    examples:
    - name: List the workload profiles from a Container Apps environment
      text: |
          az containerapp env workload-profile list -g MyResourceGroup -n MyEnvironment
"""

helps['containerapp env workload-profile show'] = """
    type: command
    short-summary: Show a workload profile from a Container Apps environment
    examples:
    - name: Show a workload profile from a Container Apps environment
      text: |
          az containerapp env workload-profile show -g MyResourceGroup -n MyEnvironment --workload-profile-name my-wlp
"""

helps['containerapp env workload-profile list-supported'] = """
    type: command
    short-summary: List the supported workload profiles in a region
    examples:
    - name: List the supported workload profiles in a region
      text: |
          az containerapp env workload-profile list-supported -l region
"""

helps['containerapp env workload-profile add'] = """
    type: command
    short-summary: Create a workload profile in a Container Apps environment
    examples:
    - name: Create a workload profile in a Container Apps environment
      text: |
          az containerapp env workload-profile add -g MyResourceGroup -n MyEnvironment --workload-profile-name my-wlp --workload-profile-type D4 --min-nodes 1 --max-nodes 2
"""

helps['containerapp env workload-profile update'] = """
    type: command
    short-summary: Update an existing workload profile in a Container Apps environment
    examples:
    - name: Update an existing workload profile in a Container Apps environment
      text: |
          az containerapp env workload-profile update -g MyResourceGroup -n MyEnvironment --workload-profile-name my-wlp --min-nodes 1 --max-nodes 3
"""

# Container Apps Job Commands
helps['containerapp job'] = """
    type: group
    short-summary: Commands to manage Container Apps jobs.
"""

helps['containerapp job create'] = """
    type: command
    short-summary: Create a container apps job.
    examples:
    - name: Create a container apps job with Trigger Type as Manual.
      text: |
          az containerapp job create -n MyContainerappsjob -g MyResourceGroup \\
              --environment MyContainerappEnv \\
              --trigger-type Manual \\
              --replica-timeout 5 \\
              --replica-retry-limit 2 \\
              --replica-completion-count 1 \\
              --parallelism 1 \\
              --image imageName \\
              --workload-profile-name my-wlp
    - name: Create a container apps job with Trigger Type as Schedule.
      text: |
          az containerapp job create -n MyContainerappsjob -g MyResourceGroup \\
              --environment MyContainerappEnv \\
              --trigger-type Schedule \\
              --replica-timeout 5 \\
              --replica-retry-limit 2 \\
              --replica-completion-count 1 \\
              --parallelism 1 \\
              --cron-expression \"*/1 * * * *\" \\
              --image imageName
    - name: Create a container apps job with Trigger Type as Event.
      text: |
          az containerapp job create -n MyContainerappsjob -g MyResourceGroup \\
              --environment MyContainerappEnv \\
              --trigger-type Event \\
              --replica-timeout 5 \\
              --replica-retry-limit 2 \\
              --replica-completion-count 1 \\
              --parallelism 1 \\
              --polling-interval 30 \\
              --min-executions 0 \\
              --max-executions 1 \\
              --scale-rule-name queue \\
              --scale-rule-type azure-queue \\
              --scale-rule-metadata "accountName=mystorageaccountname" \\
                                    "cloud=AzurePublicCloud" \\
                                    "queueLength=5" "queueName=foo" \\
              --scale-rule-auth "connection=my-connection-string-secret-name" \\
              --image imageName
"""

helps['containerapp job update'] = """
    type: command
    short-summary: Update a Container Apps Job.
    examples:
    - name: Update a job's replica timeout.
      text: |
          az containerapp job update -n my-containerapp-job -g MyResourceGroup \\
              --replica-timeout 10
"""

helps['containerapp job delete'] = """
    type: command
    short-summary: Delete a Container Apps Job.
    examples:
    - name: Delete a job.
      text: az containerapp job delete -n my-containerapp-job -g MyResourceGroup
"""

helps['containerapp job show'] = """
    type: command
    short-summary: Show details of a Container Apps Job.
    examples:
    - name: Show the details of a job.
      text: |
          az containerapp job show -n my-containerapp-job -g MyResourceGroup
"""

helps['containerapp job list'] = """
    type: command
    short-summary: List Container Apps Job by subscription or resource group.
    examples:
    - name: List jobs in the current subscription.
      text: |
          az containerapp job list
    - name: List environments by resource group.
      text: |
          az containerapp job list -g MyResourceGroup
"""

helps['containerapp job start'] = """
    type: command
    short-summary: Start a Container Apps Job execution.
    examples:
    - name: Start a job execution.
      text: az containerapp job start -n my-containerapp-job -g MyResourceGroup
    - name: Start a job with different image and configurations.
      text: az containerapp job start -n my-containerapp-job -g MyResourceGroup --image MyImageName --cpu 0.5 --memory 1.0Gi
"""

helps['containerapp job stop'] = """
    type: command
    short-summary: Stops a Container Apps Job execution.
    examples:
    - name: Stop a job execution.
      text: az containerapp job stop -n my-containerapp-job -g MyResourceGroup
    - name: Stop a job execution giving a specific job execution name.
      text: az containerapp job stop -n my-containerapp-job -g MyResourceGroup --job-execution-name MyContainerAppJob-66v9xh0
    - name: Stop all running job executions.
      text: az containerapp job stop -n my-containerapp-job -g MyResourceGroup
"""

# Container App Job Secret Commands
helps['containerapp job secret'] = """
    type: group
    short-summary: Commands to manage secrets.
"""

helps['containerapp job secret show'] = """
    type: command
    short-summary: Show details of a secret.
    examples:
    - name: Show the details of a secret.
      text: |
          az containerapp job secret show -n my-containerapp-job -g MyResourceGroup --secret-name MySecret
"""

helps['containerapp job secret list'] = """
    type: command
    short-summary: List the secrets of a container app job.
    examples:
    - name: List the secrets of a container app job.
      text: |
          az containerapp job secret list -n my-containerapp-job -g MyResourceGroup
"""

helps['containerapp job secret remove'] = """
    type: command
    short-summary: Remove secrets from a container app job.
    examples:
    - name: Remove secrets from a container app job.
      text: |
          az containerapp job secret remove -n my-containerapp-job -g MyResourceGroup --secret-names MySecret MySecret2
"""

helps['containerapp job secret set'] = """
    type: command
    short-summary: Create/update secrets.
    examples:
    - name: Add secrets to a container app job.
      text: |
          az containerapp job secret set -n my-containerapp-job -g MyResourceGroup --secrets MySecretName1=MySecretValue1 MySecretName2=keyvaultref:https://example.vault.azure.net/secrets/mysecret,identityref:/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myidentity
    - name: Update a secret.
      text: |
          az containerapp job secret set -n my-containerapp-job -g MyResourceGroup --secrets MyExistingSecretName=MyNewSecretValue MyExistingSecretName2=keyvaultref:https://example.vault.azure.net/secrets/mysecret,identityref:/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myidentity
"""

# Container App Job execution commands
helps['containerapp job execution'] = """
    type: group
    short-summary: Commands to view executions of a Container App Job.
"""

helps['containerapp job execution list'] = """
    type: command
    short-summary: Get list of all executions of a Container App Job.
    examples:
    - name: List of all executions of a Container App Job.
      text: az containerapp job execution list -n my-containerapp-job -g MyResourceGroup
"""

helps['containerapp job execution show'] = """
    type: command
    short-summary: Get execution of a Container App Job.
    examples:
    - name: Get execution of a Container App Job.
      text: az containerapp job execution show -n my-containerapp-job -g MyResourceGroup --job-execution-name MyContainerAppJob-66v9xh0
"""

# Container App Job Registry Commands
helps['containerapp job registry'] = """
    type: group
    short-summary: Commands to manage container registry information of a Container App Job.
"""

helps['containerapp job registry show'] = """
    type: command
    short-summary: Show details of a container registry from a Container App Job.
    examples:
    - name: Show the details of a container registry.
      text: |
          az containerapp job registry show -n my-containerapp-job -g MyResourceGroup --server MyContainerappJobRegistry.azurecr.io
"""

helps['containerapp job registry list'] = """
    type: command
    short-summary: List container registries configured in a Container App Job.
    examples:
    - name: List container registries configured in a Container App Job.
      text: |
          az containerapp job registry list -n my-containerapp-job -g MyResourceGroup
"""

helps['containerapp job registry set'] = """
    type: command
    short-summary: Add or update a container registry's details in a Container App Job.
    examples:
    - name: Configure a Container App Job to use a registry.
      text: |
          az containerapp job registry set -n my-containerapp-job -g MyResourceGroup \\
              --server MyContainerappJobRegistry.azurecr.io --username MyRegistryUsername --password MyRegistryPassword
"""

helps['containerapp job registry remove'] = """
    type: command
    short-summary: Remove a container registry's details in a Container App Job.
    examples:
    - name: Remove a registry from a Container App Job.
      text: |
          az containerapp job registry remove -n my-containerapp -g MyResourceGroup --server MyContainerappRegistry.azurecr.io
"""

# Certificates Commands
helps['containerapp env certificate'] = """
    type: group
    short-summary: Commands to manage certificates for the Container Apps environment.
"""

helps['containerapp env certificate create'] = """
    type: command
    short-summary: Create a managed certificate.
    examples:
    - name: Create a managed certificate.
      text: |
          az containerapp env certificate create -g MyResourceGroup --name MyEnvironment --certificate-name MyCertificate --hostname MyHostname --validation-method CNAME
"""

helps['containerapp env certificate list'] = """
    type: command
    short-summary: List certificates for an environment.
    examples:
    - name: List certificates for an environment.
      text: |
          az containerapp env certificate list -g MyResourceGroup --name MyEnvironment
    - name: Show a certificate by certificate id.
      text: |
          az containerapp env certificate list -g MyResourceGroup --name MyEnvironment --certificate MyCertificateId
    - name: List certificates by certificate name.
      text: |
          az containerapp env certificate list -g MyResourceGroup --name MyEnvironment --certificate MyCertificateName
    - name: List certificates by certificate thumbprint.
      text: |
          az containerapp env certificate list -g MyResourceGroup --name MyEnvironment --thumbprint MyCertificateThumbprint
    - name: List managed certificates for an environment.
      text: |
          az containerapp env certificate list -g MyResourceGroup --name MyEnvironment --managed-certificates-only
    - name: List private key certificates for an environment.
      text: |
          az containerapp env certificate list -g MyResourceGroup --name MyEnvironment --private-key-certificates-only
"""

helps['containerapp env certificate upload'] = """
    type: command
    short-summary: Add or update a certificate.
    examples:
    - name: Add or update a certificate.
      text: |
          az containerapp env certificate upload -g MyResourceGroup --name MyEnvironment --certificate-file MyFilepath
    - name: Add or update a certificate with a user-provided certificate name.
      text: |
          az containerapp env certificate upload -g MyResourceGroup --name MyEnvironment --certificate-file MyFilepath --certificate-name MyCertificateName
"""

helps['containerapp env certificate delete'] = """
    type: command
    short-summary: Delete a certificate from the Container Apps environment.
    examples:
    - name: Delete a certificate from the Container Apps environment by certificate name
      text: |
          az containerapp env certificate delete -g MyResourceGroup --name MyEnvironment --certificate MyCertificateName
    - name: Delete a certificate from the Container Apps environment by certificate id
      text: |
          az containerapp env certificate delete -g MyResourceGroup --name MyEnvironment --certificate MyCertificateId
    - name: Delete all certificates that have a matching thumbprint from the Container Apps environment
      text: |
          az containerapp env certificate delete -g MyResourceGroup --name MyEnvironment --thumbprint MyCertificateThumbprint
"""

# Identity Commands
helps['containerapp identity'] = """
    type: group
    short-summary: Commands to manage managed identities.
"""

helps['containerapp identity assign'] = """
    type: command
    short-summary: Assign managed identity to a container app.
    long-summary: Managed identities can be user-assigned or system-assigned.
    examples:
    - name: Assign system identity.
      text: |
          az containerapp identity assign -n my-containerapp -g MyResourceGroup --system-assigned
    - name: Assign user identity.
      text: |
          az containerapp identity assign -n my-containerapp -g MyResourceGroup --user-assigned myUserIdentityName
    - name: Assign user identity (from a different resource group than the containerapp).
      text: |
          az containerapp identity assign -n my-containerapp -g MyResourceGroup --user-assigned myUserIdentityResourceId
    - name: Assign system and user identity.
      text: |
          az containerapp identity assign -n my-containerapp -g MyResourceGroup --system-assigned --user-assigned myUserIdentityResourceId
"""

helps['containerapp identity remove'] = """
    type: command
    short-summary: Remove a managed identity from a container app.
    examples:
    - name: Remove system identity.
      text: |
          az containerapp identity remove -n my-containerapp -g MyResourceGroup --system-assigned
    - name: Remove user identity.
      text: |
          az containerapp identity remove -n my-containerapp -g MyResourceGroup --user-assigned myUserIdentityName
    - name: Remove system and user identity (from a different resource group than the containerapp).
      text: |
          az containerapp identity remove -n my-containerapp -g MyResourceGroup --system-assigned --user-assigned myUserIdentityResourceId
    - name: Remove all user identities.
      text: |
          az containerapp identity remove -n my-containerapp -g MyResourceGroup --user-assigned
    - name: Remove system identity and all user identities.
      text: |
          az containerapp identity remove -n my-containerapp -g MyResourceGroup --system-assigned --user-assigned
"""

helps['containerapp identity show'] = """
    type: command
    short-summary: Show managed identities of a container app.
    examples:
    - name: Show managed identities.
      text: |
          az containerapp identity show -n my-containerapp -g MyResourceGroup
"""

helps['containerapp job identity'] = """
    type: group
    short-summary: Commands to manage managed identities for container app job.
"""

helps['containerapp job identity assign'] = """
    type: command
    short-summary: Assign managed identity to a container app job.
    long-summary: Managed identities can be user assigned or system assigned.
    examples:
    - name: Assign system identity.
      text: |
          az containerapp job identity assign -n my-containerapp-job -g MyResourceGroup --system-assigned
    - name: Assign user identity.
      text: |
          az containerapp job identity assign -n my-containerapp-job -g MyResourceGroup --user-assigned myUserIdentityName
    - name: Assign user identity (from a different resource group than the containerapp job).
      text: |
          az containerapp job identity assign -n my-containerapp-job -g MyResourceGroup --user-assigned myUserIdentityResourceId
    - name: Assign system and user identity.
      text: |
          az containerapp job identity assign -n my-containerapp-job -g MyResourceGroup --system-assigned --user-assigned myUserIdentityResourceId
"""

helps['containerapp job identity remove'] = """
    type: command
    short-summary: Remove a managed identity from a container app job.
    examples:
    - name: Remove system identity.
      text: |
          az containerapp job identity remove -n my-containerapp-job -g MyResourceGroup --system-assigned
    - name: Remove user identity.
      text: |
          az containerapp job identity remove -n my-containerapp-job -g MyResourceGroup --user-assigned myUserIdentityName
    - name: Remove system and user identity (from a different resource group than the containerapp job).
      text: |
          az containerapp job identity remove -n my-containerapp-job -g MyResourceGroup --system-assigned --user-assigned myUserIdentityResourceId
    - name: Remove all user identities.
      text: |
          az containerapp job identity remove -n my-containerapp-job -g MyResourceGroup --user-assigned
    - name: Remove system identity and all user identities.
      text: |
          az containerapp job identity remove -n my-containerapp-job -g MyResourceGroup --system-assigned --user-assigned
"""

helps['containerapp job identity show'] = """
    type: command
    short-summary: Show managed identities of a container app job.
    examples:
    - name: Show managed identities.
      text: |
          az containerapp job identity show -n my-containerapp-job -g MyResourceGroup
"""

# Ingress Commands
helps['containerapp ingress'] = """
    type: group
    short-summary: Commands to manage ingress and traffic-splitting.
"""

helps['containerapp ingress traffic'] = """
    type: subgroup
    short-summary: Commands to manage traffic-splitting.
"""

helps['containerapp ingress show'] = """
    type: command
    short-summary: Show details of a container app's ingress.
    examples:
    - name: Show the details of a container app's ingress.
      text: |
          az containerapp ingress show -n my-containerapp -g MyResourceGroup
"""

helps['containerapp ingress enable'] = """
    type: command
    short-summary: Enable or update ingress for a container app.
    examples:
    - name: Enable or update ingress for a container app.
      text: |
          az containerapp ingress enable -n my-containerapp -g MyResourceGroup \\
              --type external --allow-insecure --target-port 80 --transport auto
"""

helps['containerapp ingress disable'] = """
    type: command
    short-summary: Disable ingress for a container app.
    examples:
    - name: Disable ingress for a container app.
      text: |
          az containerapp ingress disable -n my-containerapp -g MyResourceGroup
"""

helps['containerapp ingress update'] = """
    type: command
    short-summary: Update ingress for a container app.
    examples:
    - name: Update ingress for a container app.
      text: |
          az containerapp ingress update -n my-containerapp -g MyResourceGroup \\
              --target-port 8080
"""

helps['containerapp ingress traffic'] = """
    type: group
    short-summary: Commands to manage traffic-splitting.
"""

helps['containerapp ingress traffic set'] = """
    type: command
    short-summary: Configure traffic-splitting for a container app.
    examples:
    - name: Route 100% of a container app's traffic to its latest revision.
      text: |
          az containerapp ingress traffic set -n my-containerapp -g MyResourceGroup --revision-weight latest=100
    - name: Split a container app's traffic between two revisions.
      text: |
          az containerapp ingress traffic set -n my-containerapp -g MyResourceGroup --revision-weight latest=80 MyRevisionName=20
    - name: Split a container app's traffic between two labels.
      text: |
          az containerapp ingress traffic set -n my-containerapp -g MyResourceGroup --label-weight myLabel=80 myLabel2=20
    - name: Split a container app's traffic between a label and a revision.
      text: |
          az containerapp ingress traffic set -n my-containerapp -g MyResourceGroup --revision-weight latest=80 --label-weight myLabel=20
"""

helps['containerapp ingress traffic show'] = """
    type: command
    short-summary: Show traffic-splitting configuration for a container app.
    examples:
    - name: Show a container app's ingress traffic configuration.
      text: |
          az containerapp ingress traffic show -n my-containerapp -g MyResourceGroup
"""

helps['containerapp ingress access-restriction'] = """
    type: group
    short-summary: Commands to manage IP access restrictions.
"""

helps['containerapp ingress access-restriction set'] = """
    type: command
    short-summary: Configure IP access restrictions for a container app.
    examples:
    - name: Add an allow IP access restriction.
      text: |
          az containerapp ingress access-restriction set -n my-containerapp -g MyResourceGroup --rule-name restrictionName --ip-address 192.168.1.1/32 --description "Restriction description." --action Allow
"""

helps['containerapp ingress access-restriction remove'] = """
    type: command
    short-summary: Remove IP access restrictions from a container app.
    examples:
    - name: Remove an IP access restriction.
      text: |
          az containerapp ingress access-restriction remove -n my-containerapp -g MyResourceGroup --rule-name restrictionName
"""

helps['containerapp ingress access-restriction list'] = """
    type: command
    short-summary: List IP access restrictions for a container app.
    examples:
    - name: List IP access restrictions.
      text: |
          az containerapp ingress access-restriction list -n my-containerapp -g MyResourceGroup
"""

helps['containerapp ingress sticky-sessions'] = """
    type: group
    short-summary: Commands to set Sticky session affinity for a container app.
"""

helps['containerapp ingress sticky-sessions set'] = """
    type: command
    short-summary: Configure Sticky session for a container app.
    examples:
    - name: Set affinity to sticky for a container app.
      text: |
          az containerapp ingress sticky-sessions set -n my-containerapp -g MyResourceGroup --affinity sticky
    - name: Set affinity to none for a container app.
      text: |
          az containerapp ingress sticky-sessions set -n my-containerapp -g MyResourceGroup --affinity none
"""

helps['containerapp ingress sticky-sessions show'] = """
    type: command
    short-summary: Show the Affinity for a container app.
    examples:
    - name: Show a container app's Sticky affinity configuration.
      text: |
          az containerapp ingress sticky-sessions show -n my-containerapp -g MyResourceGroup
"""

helps['containerapp ingress cors'] = """
    type: group
    short-summary: Commands to manage CORS policy for a container app.
"""

helps['containerapp ingress cors enable'] = """
    type: command
    short-summary: Enable CORS policy for a container app.
    examples:
    - name: Set allowed origins and allowed methods for a container app.
      text: |
          az containerapp ingress cors enable -n my-containerapp -g MyResourceGroup --allowed-origins http://www.contoso.com https://www.contoso.com --allowed-methods GET POST
    - name: Set allowed origins, allowed methods and allowed headers for a container app.
      text: |
          az containerapp ingress cors enable -n my-containerapp -g MyResourceGroup --allowed-origins * --allowed-methods * --allowed-headers header1 header2
"""

helps['containerapp ingress cors disable'] = """
    type: command
    short-summary: Disable CORS policy for a container app.
    examples:
    - name: Disable CORS policy for a container app.
      text: |
          az containerapp ingress cors disable -n my-containerapp -g MyResourceGroup
"""

helps['containerapp ingress cors update'] = """
    type: command
    short-summary: Update CORS policy for a container app.
    examples:
    - name: Update allowed origins and allowed methods for a container app while keeping other cors settings.
      text: |
          az containerapp ingress cors update -n my-containerapp -g MyResourceGroup --allowed-origins http://www.contoso.com https://www.contoso.com --allowed-methods GET POST
"""

helps['containerapp ingress cors show'] = """
    type: command
    short-summary: Show CORS policy for a container app.
    examples:
    - name: Show CORS policy for a container app.
      text: |
          az containerapp ingress cors show -n my-containerapp -g MyResourceGroup
"""

# Registry Commands
helps['containerapp registry'] = """
    type: group
    short-summary: Commands to manage container registry information.
"""

helps['containerapp registry show'] = """
    type: command
    short-summary: Show details of a container registry.
    examples:
    - name: Show the details of a container registry.
      text: |
          az containerapp registry show -n my-containerapp -g MyResourceGroup --server MyContainerappRegistry.azurecr.io
"""

helps['containerapp registry list'] = """
    type: command
    short-summary: List container registries configured in a container app.
    examples:
    - name: List container registries configured in a container app.
      text: |
          az containerapp registry list -n my-containerapp -g MyResourceGroup
"""

helps['containerapp registry set'] = """
    type: command
    short-summary: Add or update a container registry's details.
    examples:
    - name: Configure a container app to use a registry.
      text: |
          az containerapp registry set -n my-containerapp -g MyResourceGroup \\
              --server MyExistingContainerappRegistry.azurecr.io --username MyRegistryUsername --password MyRegistryPassword
"""

helps['containerapp registry remove'] = """
    type: command
    short-summary: Remove a container registry's details.
    examples:
    - name: Remove a registry from a Containerapp.
      text: |
          az containerapp registry remove -n my-containerapp -g MyResourceGroup --server MyContainerappRegistry.azurecr.io
"""

# Secret Commands
helps['containerapp secret'] = """
    type: group
    short-summary: Commands to manage secrets.
"""

helps['containerapp secret show'] = """
    type: command
    short-summary: Show details of a secret.
    examples:
    - name: Show the details of a secret.
      text: |
          az containerapp secret show -n my-containerapp -g MyResourceGroup --secret-name MySecret
"""

helps['containerapp secret list'] = """
    type: command
    short-summary: List the secrets of a container app.
    examples:
    - name: List the secrets of a container app.
      text: |
          az containerapp secret list -n my-containerapp -g MyResourceGroup
"""

helps['containerapp secret remove'] = """
    type: command
    short-summary: Remove secrets from a container app.
    examples:
    - name: Remove secrets from a container app.
      text: |
          az containerapp secret remove -n my-containerapp -g MyResourceGroup --secret-names MySecret MySecret2
"""

helps['containerapp secret set'] = """
    type: command
    short-summary: Create/update secrets.
    examples:
    - name: Add secrets to a container app.
      text: |
          az containerapp secret set -n my-containerapp -g MyResourceGroup --secrets MySecretName1=MySecretValue1 MySecretName2=keyvaultref:https://example.vault.azure.net/secrets/mysecret,identityref:/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myidentity
    - name: Update a secret.
      text: |
          az containerapp secret set -n my-containerapp -g MyResourceGroup --secrets MyExistingSecretName=MyNewSecretValue MyExistingSecretName2=keyvaultref:https://example.vault.azure.net/secrets/mysecret,identityref:/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myidentity
"""

helps['containerapp github-action'] = """
    type: group
    short-summary: Commands to manage GitHub Actions.
"""

helps['containerapp github-action add'] = """
    type: command
    short-summary: Add a GitHub Actions workflow to a repository to deploy a container app.
    examples:
    - name: Add GitHub Actions, using Azure Container Registry and personal access token.
      text: az containerapp github-action add -g MyResourceGroup -n my-containerapp --repo-url https://github.com/userid/repo --branch main
          --registry-url myregistryurl.azurecr.io
          --service-principal-client-id 00000000-0000-0000-0000-00000000
          --service-principal-tenant-id 00000000-0000-0000-0000-00000000
          --service-principal-client-secret ClientSecret
          --token MyAccessToken
    - name: Add GitHub Actions, using Azure Container Registry and log in to GitHub flow to retrieve personal access token.
      text: az containerapp github-action add -g MyResourceGroup -n my-containerapp --repo-url https://github.com/userid/repo --branch main
          --registry-url myregistryurl.azurecr.io
          --service-principal-client-id 00000000-0000-0000-0000-00000000
          --service-principal-tenant-id 00000000-0000-0000-0000-00000000
          --service-principal-client-secret ClientSecret
          --login-with-github
    - name: Add GitHub Actions, using Docker Hub and log in to GitHub flow to retrieve personal access token.
      text: az containerapp github-action add -g MyResourceGroup -n my-containerapp --repo-url https://github.com/userid/repo --branch main
          --registry-username MyUsername
          --registry-password MyPassword
          --service-principal-client-id 00000000-0000-0000-0000-00000000
          --service-principal-tenant-id 00000000-0000-0000-0000-00000000
          --service-principal-client-secret ClientSecret
          --login-with-github
"""

helps['containerapp github-action delete'] = """
    type: command
    short-summary: Remove a previously configured Container Apps GitHub Actions workflow from a repository.
    examples:
    - name: Remove GitHub Actions using a personal access token.
      text: az containerapp github-action delete -g MyResourceGroup -n MyContainerapp
          --token MyAccessToken
    - name: Remove GitHub Actions using log in to GitHub flow to retrieve personal access token.
      text: az containerapp github-action delete -g MyResourceGroup -n MyContainerapp
          --login-with-github
"""

helps['containerapp github-action show'] = """
    type: command
    short-summary: Show the GitHub Actions configuration on a container app.
    examples:
    - name: Show the GitHub Actions configuration on a Containerapp.
      text: az containerapp github-action show -g MyResourceGroup -n MyContainerapp
"""

# Dapr Commands
helps['containerapp dapr'] = """
    type: group
    short-summary: Commands to manage Dapr. To manage Dapr components, see `az containerapp env dapr-component`.
"""

helps['containerapp dapr enable'] = """
    type: command
    short-summary: Enable Dapr for a container app. Updates existing values.
    examples:
    - name: Enable Dapr for a container app.
      text: |
          az containerapp dapr enable -n my-containerapp -g MyResourceGroup --dapr-app-id my-app-id --dapr-app-port 8080
"""

helps['containerapp dapr disable'] = """
    type: command
    short-summary: Disable Dapr for a container app. Removes existing values.
    examples:
    - name: Disable Dapr for a container app.
      text: |
          az containerapp dapr disable -n my-containerapp -g MyResourceGroup
"""

# custom domain Commands
helps['containerapp ssl'] = """
    type: group
    short-summary: Upload certificate to a managed environment, add hostname to an app in that environment, and bind the certificate to the hostname
"""

helps['containerapp ssl upload'] = """
    type: command
    short-summary: Upload certificate to a managed environment, add hostname to an app in that environment, and bind the certificate to the hostname
"""

helps['containerapp hostname'] = """
    type: group
    short-summary: Commands to manage hostnames of a container app.
"""

helps['containerapp hostname add'] = """
    type: command
    short-summary: Add the hostname to a container app without binding.
    examples:
    - name: Add hostname without binding.
      text: |
          az containerapp hostname add -n my-containerapp -g MyResourceGroup --hostname MyHostname
"""

helps['containerapp hostname bind'] = """
    type: command
    short-summary: Add or update the hostname and binding with a certificate.
    examples:
    - name: Add or update hostname and binding with a provided certificate.
      text: |
          az containerapp hostname bind -n my-containerapp -g MyResourceGroup --hostname MyHostname --certificate MyCertificateId
    - name: Look for or create a managed certificate and bind with the hostname if no certificate or thumbprint is provided.
      text: |
          az containerapp hostname bind -n my-containerapp -g MyResourceGroup --hostname MyHostname
"""

helps['containerapp hostname delete'] = """
    type: command
    short-summary: Delete hostnames from a container app.
    examples:
    - name: Delete secrets from a container app.
      text: |
          az containerapp hostname delete -n my-containerapp -g MyResourceGroup --hostname MyHostname
"""

helps['containerapp hostname list'] = """
    type: command
    short-summary: List the hostnames of a container app.
    examples:
    - name: List the hostnames of a container app.
      text: |
          az containerapp hostname list -n my-containerapp -g MyResourceGroup
"""

# Auth commands
helps['containerapp auth'] = """
type: group
short-summary: Manage containerapp authentication and authorization.
"""

helps['containerapp auth show'] = """
type: command
short-summary: Show the authentication settings for the containerapp.
examples:
  - name: Show the authentication settings for the containerapp.
    text: az containerapp auth show --name my-containerapp --resource-group MyResourceGroup
"""

helps['containerapp auth update'] = """
type: command
short-summary: Update the authentication settings for the containerapp.
examples:
  - name: Update the client ID of the AAD provider already configured.
    text: |
        az containerapp auth update -g myResourceGroup --name my-containerapp --set identityProviders.azureActiveDirectory.registration.clientId=my-client-id
  - name: Configure the app with file based authentication by setting the config file path.
    text: |
        az containerapp auth update -g myResourceGroup --name my-containerapp --config-file-path D:\\home\\site\\wwwroot\\auth.json
  - name: Configure the app to allow unauthenticated requests to hit the app.
    text: |
        az containerapp auth update -g myResourceGroup --name my-containerapp --unauthenticated-client-action AllowAnonymous
  - name: Configure the app to redirect unauthenticated requests to the Facebook provider.
    text: |
        az containerapp auth update -g myResourceGroup --name my-containerapp --redirect-provider Facebook
  - name: Configure the app to listen to the forward headers X-FORWARDED-HOST and X-FORWARDED-PROTO.
    text: |
        az containerapp auth update -g myResourceGroup --name my-containerapp --proxy-convention Standard
"""

helps['containerapp auth apple'] = """
type: group
short-summary: Manage containerapp authentication and authorization of the Apple identity provider.
"""

helps['containerapp auth apple show'] = """
type: command
short-summary: Show the authentication settings for the Apple identity provider.
examples:
  - name: Show the authentication settings for the Apple identity provider.
    text: az containerapp auth apple show --name my-containerapp --resource-group MyResourceGroup
"""

helps['containerapp auth apple update'] = """
type: command
short-summary: Update the client id and client secret for the Apple identity provider.
examples:
  - name: Update the client id and client secret for the Apple identity provider.
    text: |
        az containerapp auth apple update  -g myResourceGroup --name my-containerapp \\
          --client-id my-client-id --client-secret very_secret_password
"""

helps['containerapp auth facebook'] = """
type: group
short-summary: Manage containerapp authentication and authorization of the Facebook identity provider.
"""

helps['containerapp auth facebook show'] = """
type: command
short-summary: Show the authentication settings for the Facebook identity provider.
examples:
  - name: Show the authentication settings for the Facebook identity provider.
    text: az containerapp auth facebook show --name my-containerapp --resource-group MyResourceGroup
"""

helps['containerapp auth facebook update'] = """
type: command
short-summary: Update the app id and app secret for the Facebook identity provider.
examples:
  - name: Update the app id and app secret for the Facebook identity provider.
    text: |
        az containerapp auth facebook update  -g myResourceGroup --name my-containerapp \\
          --app-id my-client-id --app-secret very_secret_password
"""

helps['containerapp auth github'] = """
type: group
short-summary: Manage containerapp authentication and authorization of the GitHub identity provider.
"""

helps['containerapp auth github show'] = """
type: command
short-summary: Show the authentication settings for the GitHub identity provider.
examples:
  - name: Show the authentication settings for the GitHub identity provider.
    text: az containerapp auth github show --name my-containerapp --resource-group MyResourceGroup
"""

helps['containerapp auth github update'] = """
type: command
short-summary: Update the client id and client secret for the GitHub identity provider.
examples:
  - name: Update the client id and client secret for the GitHub identity provider.
    text: |
        az containerapp auth github update  -g myResourceGroup --name my-containerapp \\
          --client-id my-client-id --client-secret very_secret_password
"""

helps['containerapp auth google'] = """
type: group
short-summary: Manage containerapp authentication and authorization of the Google identity provider.
"""

helps['containerapp auth google show'] = """
type: command
short-summary: Show the authentication settings for the Google identity provider.
examples:
  - name: Show the authentication settings for the Google identity provider.
    text: az containerapp auth google show --name my-containerapp --resource-group MyResourceGroup
"""

helps['containerapp auth google update'] = """
type: command
short-summary: Update the client id and client secret for the Google identity provider.
examples:
  - name: Update the client id and client secret for the Google identity provider.
    text: |
        az containerapp auth google update  -g myResourceGroup --name my-containerapp \\
          --client-id my-client-id --client-secret very_secret_password
"""

helps['containerapp auth microsoft'] = """
type: group
short-summary: Manage containerapp authentication and authorization of the Microsoft identity provider.
"""

helps['containerapp auth microsoft show'] = """
type: command
short-summary: Show the authentication settings for the Azure Active Directory identity provider.
examples:
  - name: Show the authentication settings for the Azure Active Directory identity provider.
    text: az containerapp auth microsoft show --name my-containerapp --resource-group MyResourceGroup
"""

helps['containerapp auth microsoft update'] = """
type: command
short-summary: Update the client id and client secret for the Azure Active Directory identity provider.
examples:
  - name: Update the open id issuer, client id and client secret for the Azure Active Directory identity provider.
    text: |
        az containerapp auth microsoft update  -g myResourceGroup --name my-containerapp \\
          --client-id my-client-id --client-secret very_secret_password \\
          --issuer https://sts.windows.net/54826b22-38d6-4fb2-bad9-b7983a3e9c5a/
"""

helps['containerapp auth openid-connect'] = """
type: group
short-summary: Manage containerapp authentication and authorization of the custom OpenID Connect identity providers.
"""

helps['containerapp auth openid-connect show'] = """
type: command
short-summary: Show the authentication settings for the custom OpenID Connect identity provider.
examples:
  - name: Show the authentication settings for the custom OpenID Connect identity provider.
    text: az containerapp auth openid-connect show --name my-containerapp --resource-group MyResourceGroup \\
            --provider-name myOpenIdConnectProvider
"""

helps['containerapp auth openid-connect add'] = """
type: command
short-summary: Configure a new custom OpenID Connect identity provider.
examples:
  - name: Configure a new custom OpenID Connect identity provider.
    text: |
        az containerapp auth openid-connect add -g myResourceGroup --name my-containerapp \\
          --provider-name myOpenIdConnectProvider --client-id my-client-id \\
          --client-secret-name MY_SECRET_APP_SETTING \\
          --openid-configuration https://myopenidprovider.net/.well-known/openid-configuration
"""

helps['containerapp auth openid-connect update'] = """
type: command
short-summary: Update the client id and client secret setting name for an existing custom OpenID Connect identity provider.
examples:
  - name: Update the client id and client secret setting name for an existing custom OpenID Connect identity provider.
    text: |
        az containerapp auth openid-connect update -g myResourceGroup --name my-containerapp \\
          --provider-name myOpenIdConnectProvider --client-id my-client-id \\
          --client-secret-name MY_SECRET_APP_SETTING
"""

helps['containerapp auth openid-connect remove'] = """
type: command
short-summary: Removes an existing custom OpenID Connect identity provider.
examples:
  - name: Removes an existing custom OpenID Connect identity provider.
    text: |
        az containerapp auth openid-connect remove --name my-containerapp --resource-group MyResourceGroup \\
          --provider-name myOpenIdConnectProvider
"""

helps['containerapp auth twitter'] = """
type: group
short-summary: Manage containerapp authentication and authorization of the Twitter identity provider.
"""

helps['containerapp auth twitter show'] = """
type: command
short-summary: Show the authentication settings for the Twitter identity provider.
examples:
  - name: Show the authentication settings for the Twitter identity provider.
    text: az containerapp auth twitter show --name my-containerapp --resource-group MyResourceGroup
"""

helps['containerapp auth twitter update'] = """
type: command
short-summary: Update the consumer key and consumer secret for the Twitter identity provider.
examples:
  - name: Update the consumer key and consumer secret for the Twitter identity provider.
    text: |
        az containerapp auth twitter update  -g myResourceGroup --name my-containerapp \\
          --consumer-key my-client-id --consumer-secret very_secret_password
"""

# Compose commands
helps['containerapp compose'] = """
    type: group
    short-summary: Commands to create Azure Container Apps from Compose specifications.
"""

helps['containerapp compose create'] = """
    type: command
    short-summary: Create one or more Container Apps in a new or existing Container App Environment from a Compose specification.
    examples:
    - name: Create a container app by implicitly passing in a Compose configuration file from current directory.
      text: |
          az containerapp compose create -g MyResourceGroup \\
              --environment MyContainerappEnv
    - name: Create a container app by explicitly passing in a Compose configuration file.
      text: |
          az containerapp compose create -g MyResourceGroup \\
              --environment MyContainerappEnv \\
              --compose-file-path "path/to/docker-compose.yml"
"""

# Routing
helps['containerapp env http-route-config'] = """
    type: group
    short-summary: Commands to manage environment level http routing.
"""

helps['containerapp env http-route-config list'] = """
    type: command
    short-summary: List the http route configs in the environment.
    examples:
    - name: List the http route configs in the environment.
      text: |
          az containerapp env http-route-config list -g MyResourceGroup -n MyEnvironment
"""

helps['containerapp env http-route-config create'] = """
    type: command
    short-summary: Create a new http route config.
    examples:
    - name: Create a new route from a yaml file.
      text: |
          az containerapp env http-route-config create -g MyResourceGroup -n MyEnvironment -r configname --yaml config.yaml
"""

helps['containerapp env http-route-config update'] = """
    type: command
    short-summary: Update a http route config.
    examples:
    - name: Update a route in the environment from a yaml file.
      text: |
          az containerapp env http-route-config update -g MyResourceGroup -n MyEnvironment -r configname --yaml config.yaml
"""

helps['containerapp env http-route-config show'] = """
    type: command
    short-summary: Show a http route config.
    examples:
    - name: Show a route in the environment.
      text: |
          az containerapp env http-route-config show -g MyResourceGroup -n MyEnvironment -r configname
"""

helps['containerapp env http-route-config delete'] = """
    type: command
    short-summary: Delete a http route config.
    examples:
    - name: Delete a route from the environment.
      text: |
          az containerapp env http-route-config delete -g MyResourceGroup -n MyEnvironment -r configname
"""

# Ingress
helps['containerapp env premium-ingress show'] = """
    type: command
    short-summary: Show the premium ingress settings for the environment.
    examples:
    - name: Show the premium ingress settings for the environment.
      text: |
          az containerapp env premium-ingress show -g MyResourceGroup -n MyEnvironment
"""

helps['containerapp env premium-ingress'] = """
    type: group
    short-summary: Configure premium ingress settings for the environment.
    long-summary: |
        Premium ingress settings apply to all applications in the environment. They allow moving the ingress instances to a workload profile and scaling them beyond the system defaults to enable high traffic workloads. Other settings include request idle timeouts, header count limits, and the termination grace period.
    examples:
    - name: Enable premium ingress for the environment.
      text: |
          az containerapp env premium-ingress add -g MyResourceGroup -n MyEnvironment -w WorkloadProfileName
"""

helps['containerapp env premium-ingress add'] = """
    type: command
    short-summary: Enable the premium ingress settings for the environment.
    long-summary: |
        Unspecified optional parameters will be cleared from any existing configuration.
    examples:
    - name: Add the premium ingress settings for the environment.
      text: |
          az containerapp env premium-ingress add -g MyResourceGroup -n MyEnvironment -w WorkloadProfileName
"""

helps['containerapp env premium-ingress update'] = """
    type: command
    short-summary: Update the premium ingress settings for the environment.
    examples:
    - name: Update the workload profile used for premium ingress.
      text: |
          az containerapp env premium-ingress update -g MyResourceGroup -n MyEnvironment -w WorkloadProfileName
"""

helps['containerapp env premium-ingress remove'] = """
    type: command
    short-summary: Remove the ingress settings and restores the system to default values.
    examples:
    - name: Reset the ingress settings for the environment to its default values
      text: |
          az containerapp env premium-ingress remove -g MyResourceGroup -n MyEnvironment
"""
