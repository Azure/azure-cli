# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['deploymentmanager'] = """
type: group
short-summary: Create and manage rollouts for your service.
long-summary: To deploy your service across many regions and make sure it is running as expected in each region, you can use deployment manager to coordinate a staged rollout of the service. For more details, visit https://docs.microsoft.com/azure/azure-resource-manager/deployment-manager-overview
"""

helps['deploymentmanager artifact-source'] = """
type: group
short-summary: Manage artifact sources.
long-summary: Artifact sources can be used for creating service topologies and rollouts.
"""

helps['deploymentmanager artifact-source create'] = """
type: command
short-summary: Creates an artifact source.
examples:
  - name: Create a new artifact source.
    text: az deploymentmanager artifact-source create -g rg1 -n contosoServiceArtifactSource -l location --sas-uri https://myStorageAct.blob.azure.com/artifacts?st=2019-04-10T22%3A12Z&se=2019-04-11T09%3A12Z&sp=rl&sv=2018-03-28&sr=c&sig=f6Nx8en4sIJQryYFVVj%2B5BdU7bho96jAgOzLO40Twkg%3D
"""

helps['deploymentmanager artifact-source delete'] = """
type: command
short-summary: Deletes an artifact source.
examples:
  - name: Deletes an artifact source
    text: >
        az deploymentmanager artifact-source delete -g rg1 -n contosoServiceArtifactSource
"""

helps['deploymentmanager artifact-source show'] = """
type: command
short-summary: Get the details of an artifact source.
examples:
  - name: Get an artifact source
    text: >
        az deploymentmanager artifact-source show -g rg1 -n contosoServiceArtifactSource
"""

helps['deploymentmanager artifact-source list'] = """
type: command
short-summary: List all artifact sources in a resource group.
examples:
  - name: List artifact sources in the given resource group.
    text: >
        az deploymentmanager artifact-source list -g rg1
"""

helps['deploymentmanager artifact-source update'] = """
type: command
short-summary: Updates an artifact source.
examples:
  - name: Updates an artifact source
    text: >
        az deploymentmanager artifact-source update -g rg1 -n contosoServiceArtifactSource --sas-uri https://dummy.blob.azure.com/updated_sample_sas_uri
"""

helps['deploymentmanager rollout'] = """
type: group
short-summary: Manage the rollouts.
long-summary: View progress, restart a failed rollout, stop a running rollout. Rollouts can be created using the 'az group deployment' command.
"""

helps['deploymentmanager rollout restart'] = """
type: command
short-summary: Restarts the rollout.
examples:
  - name: Restart the rollout
    text: >
        az deploymentmanager rollout restart -g rg1 -n contosoServiceRollout

  - name: Restart the rollout and skip all steps that have succeeded in the previous run
    text: >
        az deploymentmanager rollout restart -g rg1 -n contosoServiceRollout --skip-succeeded
"""

helps['deploymentmanager rollout show'] = """
type: command
short-summary: Gets the rollout.
examples:
  - name: Gets the rollout
    text: >
        az deploymentmanager rollout show -g rg1 -n contosoServiceRollout
  - name: Gets the specific retry attempt of a rollout. Shows the steps run during that attempt.
    text: >
        az deploymentmanager rollout show -g rg1 -n contosoServiceRollout --retry-attempt 1
"""

helps['deploymentmanager rollout list'] = """
type: command
short-summary: List all rollouts in a resource group
examples:
  - name: List all rollouts in the resource group
    text: >
        az deploymentmanager rollout list -g rg1
"""

helps['deploymentmanager rollout stop'] = """
type: command
short-summary: Stop the rollout.
examples:
  - name: Stops the rollout
    text: >
        az deploymentmanager rollout stop -g rg1 -n contosoServiceRollout
"""

helps['deploymentmanager service'] = """
type: group
short-summary: Manage the services in a service topology.
"""

helps['deploymentmanager service create'] = """
type: command
short-summary: Creates a service under the specified service topology.
examples:
  - name: Create a new service under a service topology. Specify the service by its name, service topology it is in and the resource group name.
    text: >
        az deploymentmanager service create -g rg1 -l serviceLocation --service-topology-name contosoServiceTopology -n contosoService1 --target-location "East US" --target-subscription-id XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
"""

helps['deploymentmanager service delete'] = """
type: command
short-summary: Deletes the service topology.
examples:
  - name: Deletes a service topology.
    text: >
        az deploymentmanager service delete -g rg1 --service-topology-name contosoServiceTopology -n contosoService1
"""

helps['deploymentmanager service show'] = """
type: command
short-summary: Get the details of a service.
examples:
  - name: Get the service under a service topology.
    text: >
        az deploymentmanager service show -g rg1 --service-topology-name contosoServiceTopology -n contosoService1
"""

helps['deploymentmanager service list'] = """
type: command
short-summary: List all services in a service topology.
examples:
  - name: List all the services under the given service topology.
    text: >
        az deploymentmanager service list -g rg1 --service-topology-name contosoServiceTopology
"""

helps['deploymentmanager service update'] = """
type: command
short-summary: Updates the service.
examples:
  - name: Updates the service.
    text: >
        az deploymentmanager service update -g rg1 --service-topology-name contosoServiceTopology -n contosoService1 --target-location "West US" --target-subscription-id XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
"""

helps['deploymentmanager service-topology'] = """
type: group
short-summary: Manage service topologies.
"""

helps['deploymentmanager service-topology create'] = """
type: command
short-summary: Creates a service topology.
examples:
  - name: Create a new service topology.
    text: >
        az deploymentmanager service-topology create -g rg1 -l topologyLocation -n contosoServiceTopology --artifact-source /subscriptions/mySub/resourcegroups/rg1/providers/Microsoft.DeploymentManager/artifactSources/contosoWebAppArtifactSource
"""

helps['deploymentmanager service-topology delete'] = """
type: command
short-summary: Deletes the service topology.
examples:
  - name: Deletes a service topology.
    text: >
        az deploymentmanager service-topology delete -g rg1 -n contosoServiceTopology
"""

helps['deploymentmanager service-topology show'] = """
type: command
short-summary: Get the details of a service topology.
examples:
  - name: Get the service topology.
    text: >
        az deploymentmanager service-topology show -g rg1 -n contosoServiceTopology
"""

helps['deploymentmanager service-topology list'] = """
type: command
short-summary: List all service topologies in a resource group.
examples:
  - name: List all the service topologies in the resource group.
    text: >
        az deploymentmanager service-topology list -g rg1
"""

helps['deploymentmanager service-topology update'] = """
type: command
short-summary: Updates the service topology.
examples:
  - name: Updates the service topology.
    text: >
        az deploymentmanager service-topology update -g rg1 -n contosoServiceTopology --artifact-source /subscriptions/mySub/resourcegroups/rg1/providers/Microsoft.DeploymentManager/artifactSources/contosoWebAppArtifactSource
"""

helps['deploymentmanager service-unit'] = """
type: group
short-summary: Manage the service units.
long-summary: Service units combine to form a service in a service topology.
"""

helps['deploymentmanager service-unit create'] = """
type: command
short-summary: Creates a service unit under the specified service and service topology.
examples:
  - name: Create a new service unit using relative paths into the artifact source.
    description: Specify the service unit by its name, the service and service topology it is in. The template and parameters files are defined as relative paths into the artifact source location referenced in the specified service topology. The resources defined in this template are to be deployed into the target resource group service1ResourceGroup with the deployment mode set to 'Incremental'.
    text: >
        az deploymentmanager service-unit create -g rg1 -l location --service-topology-name contosoServiceTopology --service-name contosoService1 -n ContosoService1Storage --target-resource-group service1ResourceGroup --deployment-mode Incremental --template-path "Templates/Service1.Storage.json" --parameters-path "Parameters/Service1.Storage.Parameters.json"
  - name: Create a new service unit using SAS Uri for template and parameters.
    description: Specify the service unit by its name, the service and service topology it is in. The template and parameters files are defined as SAS Uri's. The resources defined in this template are to be deployed into the target resource group service1ResourceGroup with the deployment mode set to 'Incremental'.
    text: >
        az deploymentmanager service-unit create -g rg1 -l location --service-topology-name contosoServiceTopology --service-name contosoService1 -n ContosoService1Storage \\
            --target-resource-group service1ResourceGroup --deployment-mode Incremental \\
            --template-path "https://ContosoStorage.blob.core.windows.net/ContosoArtifacts/Templates/Service2.Storage.json?sasParameters" \\
            --parameters-path "https://ContosoStorage.blob.core.windows.net/ContosoArtifacts/Parameters/Service2Storage.Parameters.json?sasParameters"
"""

helps['deploymentmanager service-unit delete'] = """
type: command
short-summary: Deletes the service unit.
examples:
  - name: Deletes a service unit.
    text: >
        az deploymentmanager service-unit delete -g rg1 --service-topology-name contosoServiceTopology --service-name contosoService1 -n ContosoService1Storage
"""

helps['deploymentmanager service-unit show'] = """
type: command
short-summary: Get the details of a service unit.
examples:
  - name: Get the service unit.
    text: >
        az deploymentmanager service-unit show -g rg1 --service-topology-name contosoServiceTopology --service-name contosoService1 -n ContosoService1Storage
"""

helps['deploymentmanager service-unit list'] = """
type: command
short-summary: List all service units in a service.
examples:
  - name: List the service units in the given service topology and service.
    text: >
        az deploymentmanager service-unit list -g rg1 --service-topology-name contosoServiceTopology --service-name contosoService1
"""

helps['deploymentmanager service-unit update'] = """
type: command
short-summary: Updates the service unit.
examples:
  - name: Updates the service unit.
    text: >
        az deploymentmanager service-unit update -g rg1 --service-topology-name contosoServiceTopology --service-name contosoService1 -n ContosoService1Storage --target-resource-group service1ResourceGroupUpdated
  - name: Updates the service unit. (autogenerated)
    text: az deploymentmanager service-unit update --deployment-mode Incremental --resource-group rg1 --service-name contosoService1 --service-topology-name contosoServiceTopology --service-unit-name ContosoService1Storage
    crafted: true
"""

helps['deploymentmanager step'] = """
type: group
short-summary: Manage the steps.
long-summary: Allows you to manage the steps that can be used in rollouts.
"""

helps['deploymentmanager step create'] = """
type: command
short-summary: Creates the step.
examples:
  - name: Creates a wait step.
    text: >
        az deploymentmanager step create -g rg1 -l location -n contosoServiceWaitStep --duration PT30M
  - name: Creates a health check step from a JSON file. The step information is read from the file.
    text: >
        az deploymentmanager step create -g rg1 --step healthcheck_step.json
"""

helps['deploymentmanager step show'] = """
type: command
short-summary: Get the details of the step.
examples:
  - name: Get the step.
    text: >
        az deploymentmanager step show -g rg1 -n contosoServiceWaitStep
"""

helps['deploymentmanager step list'] = """
type: command
short-summary: List all steps in a resource group.
examples:
  - name: List available steps in the given resource group.
    text: >
        az deploymentmanager step list -g rg1
"""

helps['deploymentmanager step update'] = """
type: command
short-summary: Updates the step.
examples:
  - name: Updates a step.
    text: >
        az deploymentmanager step update -g rg1 -n contosoServiceWaitStep --duration PT20M
"""
