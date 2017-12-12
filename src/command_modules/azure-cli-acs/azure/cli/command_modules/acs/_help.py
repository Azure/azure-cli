# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps
import os.path

SERVICE_PRINCIPAL_CACHE = os.path.join('$HOME', '.azure', 'acsServicePrincipal.json')


# ACS command help

helps['acs'] = """
     type: group
     short-summary: Manage Azure container services.
"""

helps['acs browse'] = """
    type: command
    short-summary: Open a web browser to the dashboard for a container service's orchestrator.
"""

helps['acs create'] = """
    type: command
    short-summary: Create a new container service.
    parameters:
        - name: --service-principal
          type: string
          short-summary: Service principal used for authentication to Azure APIs. If not specified, a new service
                         principal with contributor role is created and cached at {sp_cache} to be used by subsequent
                         `az acs` commands.
        - name: --client-secret
          type: string
          short-summary: Secret associated with a service principal. This argument is required if `--service-principal`
                         is specified.
        - name: --agent-count
          short-summary: Set default number of agents for the agent pools.
                         Note that DC/OS clusters will have 1 or 2 additional public agents.
    examples:
        - name: Create a default acs cluster.
          text: az acs create -g MyResourceGroup -n MyContainerService
        - name: Create a Kubernetes cluster.
          text: az acs create --orchestrator-type Kubernetes -g MyResourceGroup -n MyContainerService
        - name: Create a Kubernetes cluster with a an existing SSH key.
          text: >-
              az acs create --orchestrator-type Kubernetes -g MyResourceGroup -n MyContainerService
                --ssh-key-value /path/to/publickey
        - name: Create an ACS cluster with two agent pools.
          text: >-
              az acs create -g MyResourceGroup -n MyContainerService
                --agent-profiles "[{{'name':'agentpool1'}},{{'name':'agentpool2'}}]"
        - name: Create an ACS cluster where the second agent pool has a vmSize specified.
          text: >-
              az acs create -g MyResourceGroup -n MyContainerService
                --agent-profiles "[{{'name':'agentpool1'}},{{'name':'agentpool2','vmSize':'Standard_D2'}}]"
        - name: Create an ACS cluster with agent-profiles specified from a file.
          text: az acs create -g MyResourceGroup -n MyContainerService --agent-profiles MyAgentProfiles.json
""".format(sp_cache=SERVICE_PRINCIPAL_CACHE)

helps['acs dcos'] = """
    type: group
    short-summary: Commands to manage a DC/OS-orchestrated Azure container service.
"""

helps['acs install-cli'] = """
    type: command
    short-summary: Download and install the DC/OS or Kubernetes command-line tool for a cluster.
"""

helps['acs kubernetes'] = """
    type: group
    short-summary: Commands to manage a Kubernetes-orchestrated Azure container service.
"""

helps['acs kubernetes get-credentials'] = """
    type: command
    short-summary: Download and install credentials to access a cluster.
"""

helps['acs list-locations'] = """
    type: command
    short-summary: List locations where Azure container service is in preview and in production.
"""

helps['acs scale'] = """
    type: command
    short-summary: Change the private agent count of a container service.
    parameters:
        - name: --new-agent-count
          type: int
          short-summary: The number of agents for the container service.
"""

helps['acs show'] = """
    type: command
    short-summary: Show details of a container service.
"""

helps['acs wait'] = """
    type: command
    short-summary: Wait for a container service to reach a desired state.
"""

# AKS command help

helps['aks'] = """
     type: group
     short-summary: Manage Azure Kubernetes clusters.
"""

helps['aks browse'] = """
    type: command
    short-summary: Open a web browser to the dashboard for a managed Kubernetes cluster.
    parameters:
        - name: --disable-browser
          type: bool
          short-summary: Don't launch a web browser after establishing port-forwarding.
"""

helps['aks create'] = """
    type: command
    short-summary: Create a new managed Kubernetes cluster.
    parameters:
        - name: --generate-ssh-keys
          type: string
          short-summary: Generate SSH public and private key files if missing.
        - name: --service-principal
          type: string
          short-summary: Service principal used for authentication to Azure APIs. If not specified, a new service
                         principal with contributor role is created and cached at {sp_cache} to be used by subsequent
                         `az aks` commands.
        - name: --client-secret
          type: string
          short-summary: Secret associated with a service principal. This argument is required if `--service-principal`
                         is specified.
        - name: --node-vm-size -s
          type: string
          short-summary: Size of Virtual Machines to create as Kubernetes nodes.
        - name: --dns-name-prefix -p
          type: string
          short-summary: Prefix for hostnames that are created. If not specified, gemerate a hostname using the
                         managed cluster and resource group names.
        - name: --node-count -c
          type: int
          short-summary: Number of nodes in the Kubernetes node pool. After creating a cluster, you can change the
                         size of its node pool with `az aks scale`.
        - name: --node-osdisk-size
          type: int
          short-summary: Size in GB of the OS disk for each node in the node pool.
        - name: --kubernetes-version -k
          type: string
          short-summary: Version of Kubernetes to use for creating the cluster, such as "1.7.7" or "1.8.2".
        - name: --ssh-key-value
          type: string
          short-summary: Public key path or key contents to install on node VMs for SSH access. For example,
                         'ssh-rsa AAAAB...snip...UcyupgH azureuser@linuxvm'.
        - name: --admin-username -u
          type: string
          short-summary: User account to create on node VMs for SSH access.
    examples:
        - name: Create a Kubernetes cluster.
          text: az aks create -g MyResourceGroup -n MyManagedCluster
        - name: Create a Kubernetes cluster with an existing SSH key.
          text: az aks create -g MyResourceGroup -n MyManagedCluster --ssh-key-value /path/to/publickey
        - name: Create a Kubernetes cluster with a specific version.
          text: az aks create -g MyResourceGroup -n MyManagedCluster --kubernetes-version 1.8.1
        - name: Create a Kubernetes cluster with a larger node pool.
          text: az aks create -g MyResourceGroup -n MyManagedCluster --node-count 7
""".format(sp_cache=SERVICE_PRINCIPAL_CACHE)

helps['aks delete'] = """
    type: command
    short-summary: Delete a managed Kubernetes cluster.
"""

helps['aks get-credentials'] = """
    type: command
    short-summary: Get access credentials for a managed Kubernetes cluster.
    parameters:
        - name: --admin -a
          type: bool
          short-summary: "Get cluster administrator credentials.  Default: cluster user credentials."
        - name: --file -f
          type: string
          short-summary: Kubernetes configuration file to update. Use "-" to print YAML to stdout instead.
"""

helps['aks get-versions'] = """
    type: command
    short-summary: Get versions available to upgrade a managed Kubernetes cluster.
"""

helps['aks install-cli'] = """
    type: command
    short-summary: Download and install kubectl, the Kubernetes command-line tool.
"""

helps['aks wait'] = """
    type: command
    short-summary: Wait for a Kubernetes cluster to reach a desired state.
"""

helps['aks install-connector'] = """
    type: command
    short-summary: Install the ACI Connector to a managed Kubernetes cluster.
    long-summary: |
        Allows the cluster to deploy Azure Container Instances.
        See https://github.com/Azure/aci-connector-k8s for more details.
    parameters:
        - name: --chart-url
          type: string
          short-summary: URL of a Helm chart that installs ACI Connector.
        - name: --connector-name
          type: string
          short-summary: Name of the ACI Connector.
        - name: --os-type
          type: string
          short-summary: Install support for deploying ACIs of this operating system type.
        - name: --service-principal
          type: string
          short-summary: Service principal used for authentication to Azure APIs. If not specified, a new service
                         principal with contributor role is created and cached at {sp_cache} to be used by subsequent
                         `az aks` commands.
        - name: --client-secret
          type: string
          short-summary: Secret associated with a service principal. This argument is required if `--service-principal`
                         is specified.
    examples:
        - name: Install the ACI Connector to a managed Kubernetes cluster.
          text: >-
            az aks install-connector --name MyManagedCluster --resource-group MyResourceGroup
            --connector-name MyConnector
        - name: Install the ACI Connector for Windows to a managed Kubernetes cluster.
          text: az aks install-connector --name MyManagedCluster --resource-group MyResourceGroup --connector-name MyConnector --os-type Windows
        - name: Install the ACI Connector for Windows and Linux to a managed Kubernetes cluster.
          text: az aks install-connector --name MyManagedCluster --resource-group MyResourceGroup --connector-name MyConnector --os-type Both
        - name: Install the ACI Connector using a specific service principal and secret.
          text: az aks install-connector --name MyManagedCluster --resource-group MyResourceGroup --connector-name MyConnector --service-principal <SPN_ID> --client-secret <SPN_SECRET>
        - name: Install the ACI Connector from a custom Helm chart.
          text: az aks install-connector --name MyManagedCluster --resource-group MyResourceGroup --connector-name MyConnector --chart-url <CustomURL>
""".format(sp_cache=SERVICE_PRINCIPAL_CACHE)

helps['aks list'] = """
    type: command
    short-summary: List managed Kubernetes clusters.
"""

helps['aks remove-connector'] = """
    type: command
    short-summary: Remove the ACI Connector from a managed Kubernetes cluster.
    long-summary: |-
        Stops the cluster from deploying Azure Container Instances.
        See https://github.com/Azure/aci-connector-k8s for more details.
    parameters:
        - name: --connector-name
          type: string
          short-summary: Name of the ACI Connector.
        - name: --graceful
          type: bool
          short-summary: Use a "cordon and drain" strategy to evict pods safely before removing the ACI node.
        - name: --os-type
          type: string
          short-summary: Remove support for deploying ACIs of this operating system type.
    examples:
        - name: Remove the ACI Connector from a managed Kubernetes cluster.
          text: az aks remove-connector --name MyManagedCluster --resource-group MyResourceGroup --connector-name MyConnector
        - name: Remove the ACI Connector from a cluster using the graceful mode.
          text: az aks remove-connector --name MyManagedCluster --resource-group MyResourceGroup --connector-name MyConnector --graceful
"""

helps['aks scale'] = """
    type: command
    short-summary: Scale the node pool in a managed Kubernetes cluster.
    parameters:
        - name: --node-count -c
          type: int
          short-summary: Number of nodes in the Kubernetes node pool.
"""

helps['aks show'] = """
    type: command
    short-summary: Show details of a managed Kubernetes cluster.
"""

helps['aks upgrade'] = """
    type: command
    short-summary: Upgrade a managed Kubernetes cluster to a newer version.
    long-summary: "NOTE: Kubernetes may be unavailable during cluster upgrades."
    parameters:
        - name: --kubernetes-version -k
          type: string
          short-summary: Version of Kubernetes to upgrade the cluster to, such as "1.7.7" or "1.8.2".
          populator-commands:
          - "`az aks get-versions`"
"""

helps['aks wait'] = """
    type: command
    short-summary: Wait for a managed Kubernetes cluster to reach a desired state.
    long-summary: If an operation on a cluster was interrupted or was started with `--no-wait`, use this command to
                  wait for it to complete.
    examples:
        - name: Wait for a cluster to be created.
          text: |-
            az aks create -g MyResourceGroup -n MyManagedCluster --no-wait
            az aks wait -g MyResourceGroup -n MyManagedCluster --created
        - name: Wait for a cluster to be deleted.
          text: |-
            az aks delete -g MyResourceGroup -n MyManagedCluster --no-wait --yes
            az aks wait -g MyResourceGroup -n MyManagedCluster --deleted
        - name: Wait for a cluster's node pool to scale up.
          text: |-
            az aks scale -g MyResourceGroup -n MyManagedCluster --node-count 7 --no-wait
            az aks wait -g MyResourceGroup -n MyManagedCluster --updated
        - name: Wait for a cluster to be upgraded, polling every minute for up to thirty minutes.
          text: |-
            az aks upgrade -g MyResourceGroup -n MyManagedCluster -k 1.8.2 --no-wait --yes
            az aks wait -g MyResourceGroup -n MyManagedCluster --updated --interval 60 --timeout 1800
"""
