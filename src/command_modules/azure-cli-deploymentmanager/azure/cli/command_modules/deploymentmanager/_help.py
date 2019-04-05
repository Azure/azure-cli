# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['deploymentmanager'] = """
    type: group
    short-summary: Create and manage rollouts for your service.
    long-summary: To deploy your service across many regions and make sure it is running as expected in each region, you can use deployment manager to coordinate a staged rollout of the service. For more details, visit https://docs.microsoft.com/en-us/azure/azure-resource-manager/deployment-manager-overview
"""

helps['deploymentmanager artifact-source create'] = """
    type: command
    short-summary: Creates an artifact source.
    examples:
        - name: Create a new artifact source.
          text: az deploymentmanager artifact-source create -g rg1 --artifact-source-name contosoServiceArtifactSource -l centralus --sas-uri https://dummy.blob.azure.com/samplesasuri
"""

helps['deploymentmanager artifact-source show'] = """
    type: command
    short-summary: Get the details of an artifact source.
    examples:
        - name: Get an artifact source
          text: >
            az deploymentmanager artifact-source show -g rg1 --artifact-source-name contosoServiceArtifactSource
"""

helps['deploymentmanager artifact-source delete'] = """
    type: command
    short-summary: Deletes an artifact source.
    examples:
        - name: Deletes an artifact source
          text: >
            az deploymentmanager artifact-source delete -g rg1 --artifact-source-name contosoServiceArtifactSource
"""

helps['deploymentmanager artifact-source update'] = """
    type: command
    short-summary: Updates an artifact source.
    examples:
        - name: Updates an artifact source
          text: >
            az deploymentmanager artifact-source update -g rg1 --artifact-source-name contosoServiceArtifactSource --sas-uri https://dummy.blob.azure.com/updated_sample_sas_uri
"""

helps['deploymentmanager service-topology create'] = """
    type: command
    short-summary: Creates a service topology.
    examples:
        - name: Create a new service topology.
          text: >
            az deploymentmanager service-topology create -g rg1 --service-topology-name contosoServiceTopology --artifact-source-id /subscriptions/mySub/resourcegroups/rg1/providers/Microsoft.DeploymentManager/artifactSources/contosoWebAppArtifactSource 
"""

helps['deploymentmanager service-topology show'] = """
    type: command
    short-summary: Get the details of a service topology.
    examples:
        - name: Get the service topology.
          text: >
            az deploymentmanager service-topology show -g rg1 --service-topology-name contosoServiceTopology 
"""

helps['deploymentmanager service-topology delete'] = """
    type: command
    short-summary: Deletes the service topology.
    examples:
        - name: Deletes a service topology.
          text: >
            az deploymentmanager service-topology delete -g rg1 --service-topology-name contosoServiceTopology 
"""

helps['deploymentmanager service-topology update'] = """
    type: command
    short-summary: Updates the service topology.
    examples:
        - name: Updates the service topology.
          text: >
            az deploymentmanager service-topology update -g rg1 --service-topology-name contosoServiceTopology --artifact-source-id /subscriptions/mySub/resourcegroups/rg1/providers/Microsoft.DeploymentManager/artifactSources/contosoWebAppArtifactSource 
"""

helps['deploymentmanager service create'] = """
    type: command
    short-summary: Creates a service under the specified service topology.
    examples:
        - name: Create a new service under a service topology. Specify the service by its name, service topology it is in and the resource group name.
          text: >
            az deploymentmanager service create -g rg1 -location centralus --service-topology-name contosoServiceTopology --service-name contosoService1 --target-location "East US" --target-subscription-id XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
"""

helps['deploymentmanager service show'] = """
    type: command
    short-summary: Get the details of a service.
    examples:
        - name: Get the service under a service topology.
          text: >
            az deploymentmanager service show -g rg1 --service-topology-name contosoServiceTopology --service-name contosoService1
"""

helps['deploymentmanager service delete'] = """
    type: command
    short-summary: Deletes the service topology.
    examples:
        - name: Deletes a service topology.
          text: >
            az deploymentmanager service delete -g rg1 --service-topology-name contosoServiceTopology --service-name contosoService1
"""

helps['deploymentmanager service update'] = """
    type: command
    short-summary: Updates the service.
    examples:
        - name: Updates the service.
          text: >
            az deploymentmanager service update -g rg1 --service-topology-name contosoServiceTopology --service-name contosoService1 --target-location "West US" --target-subscription-id XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
"""

helps['deploymentmanager service-unit create'] = """
    type: command
    short-summary: Creates a service unit under the specified service and service topology.
    examples:
        - name: Create a new service unit using relative paths into the artifact source.
          description:
            Specify the service unit by its name, the service and service topology it is in. 
            The template and parameters files are defined as relative paths into the artifact source location referenced in the specified service topology.
            The resources defined in this template are to be deployed into the target resource group service1ResourceGroup with the deployment mode set to 'Incremental'.
          text: >
            az deploymentmanager service-unit create -g rg1 -location centralus --service-topology-name contosoServiceTopology --service-name contosoService1 --service-unit-name ContosoService1Storage --target-resource-group service1ResourceGroup --deployment-mode Incremental --template-artifact-source-relative-path "Templates/Service1.Storage.json" --parameters-artifact-source-relative-path "Parameters/Service1.Storage.Parameters.json" 
        - name: Create a new service unit using SAS Uri for template and parameters.
          description:
            Specify the service unit by its name, the service and service topology it is in. 
            The template and parameters files are defined as SAS Uri's.
            The resources defined in this template are to be deployed into the target resource group service1ResourceGroup with the deployment mode set to 'Incremental'.
          text: >
            az deploymentmanager service-unit create -g rg1 -location centralus --service-topology-name contosoServiceTopology --service-name contosoService1 --service-unit-name ContosoService1Storage \\
                --target-resource-group service1ResourceGroup --deployment-mode Incremental \\
                --template-uri "https://ContosoStorage.blob.core.windows.net/ContosoArtifacts/Templates/Service2.Storage.json?sasParameters" \\
                --parameters-uri "https://ContosoStorage.blob.core.windows.net/ContosoArtifacts/Parameters/Service2Storage.Parameters.json?sasParameters"
"""

helps['deploymentmanager service-unit show'] = """
    type: command
    short-summary: Get the details of a service unit.
    examples:
        - name: Get the service unit.
          text: >
            az deploymentmanager service-unit show -g rg1 -location centralus --service-topology-name contosoServiceTopology --service-name contosoService1 --service-unit-name ContosoService1Storage
"""

helps['deploymentmanager service-unit delete'] = """
    type: command
    short-summary: Deletes the service unit.
    examples:
        - name: Deletes a service unit.
          text: >
            az deploymentmanager service-unit delete -g rg1 -location centralus --service-topology-name contosoServiceTopology --service-name contosoService1 --service-unit-name ContosoService1Storage
"""

helps['deploymentmanager service-unit update'] = """
    type: command
    short-summary: Updates the service unit.
    examples:
        - name: Updates the service unit.
          text: >
            az deploymentmanager service-unit update -g rg1 -location centralus --service-topology-name contosoServiceTopology --service-name contosoService1 --service-unit-name ContosoService1Storage --target-resource-group service1ResourceGroupUpdated
"""