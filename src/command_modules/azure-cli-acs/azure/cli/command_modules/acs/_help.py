# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path

from knack.help_files import helps

ACS_SERVICE_PRINCIPAL_CACHE = os.path.join('$HOME', '.azure', 'acsServicePrincipal.json')
AKS_SERVICE_PRINCIPAL_CACHE = os.path.join('$HOME', '.azure', 'aksServicePrincipal.json')


# ACS command help

helps['acs'] = """
     type: group
     short-summary: Manage Azure Container Services.
"""

helps['acs browse'] = """
    type: command
    short-summary: Show the dashboard for a service container's orchestrator in a web browser.
"""

helps['acs create'] = """
    type: command
    short-summary: Create a new container service.
    parameters:
        - name: --service-principal
          type: string
          short-summary: Service principal used for authentication to Azure APIs.
          long-summary:  If not specified, a new service principal with the contributor role is created and cached at
                         {sp_cache} to be used by subsequent `az acs` commands.
        - name: --client-secret
          type: string
          short-summary: Secret associated with the service principal. This argument is required if
                         `--service-principal` is specified.
        - name: --agent-count
          short-summary: Set the default number of agents for the agent pools.
          long-summary: Note that DC/OS clusters will have 1 or 2 additional public agents.
    examples:
        - name: Create a DCOS cluster with an existing SSH key.
          text: |-
              az acs create --orchestrator-type DCOS -g MyResourceGroup -n MyContainerService \\
                --ssh-key-value /path/to/publickey
        - name: Create a DCOS cluster with two agent pools.
          text: |-
              az acs create -g MyResourceGroup -n MyContainerService --agent-profiles '[
                {{
                  "name": "agentpool1"
                }},
                {{
                  "name": "agentpool2"
                }}]'
        - name: Create a DCOS cluster where the second agent pool has a vmSize specified.
          text: |-
              az acs create -g MyResourceGroup -n MyContainerService --agent-profiles '[
                {{
                  "name": "agentpool1"
                }},
                {{
                  "name": "agentpool2",
                  "vmSize": "Standard_D2"
                }}]'
        - name: Create a DCOS cluster with agent-profiles specified from a file.
          text: az acs create -g MyResourceGroup -n MyContainerService --agent-profiles MyAgentProfiles.json
""".format(sp_cache=ACS_SERVICE_PRINCIPAL_CACHE)

helps['acs dcos'] = """
    type: group
    short-summary: Commands to manage a DC/OS-orchestrated Azure Container Service.
"""

helps['acs dcos install-cli'] = """
    type: command
    short-summary: Download and install the DC/OS command-line tool for a cluster.
"""

helps['acs kubernetes install-cli'] = """
    type: command
    short-summary: Download and install the Kubernetes command-line tool for a cluster.
"""

helps['acs kubernetes'] = """
    type: group
    short-summary: Commands to manage a Kubernetes-orchestrated Azure Container Service.
"""

helps['acs kubernetes get-credentials'] = """
    type: command
    short-summary: Download and install credentials to access a cluster.  This command requires
                   the same private-key used to create the cluster.
"""

helps['acs list-locations'] = """
    type: command
    short-summary: List locations where Azure Container Service is in preview and in production.
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
    short-summary: Show the details for a container service.
"""

helps['acs wait'] = """
    type: command
    short-summary: Wait for a container service to reach a desired state.
    long-summary: If an operation on a container service was interrupted or was started with `--no-wait`, use this
                  command to wait for it to complete.
"""

# AKS command help

helps['aks'] = """
     type: group
     short-summary: (PREVIEW) Manage Azure Kubernetes Services.
"""

helps['aks browse'] = """
    type: command
    short-summary: (PREVIEW) Show the dashboard for a Kubernetes cluster in a web browser.
    parameters:
        - name: --disable-browser
          type: bool
          short-summary: Don't launch a web browser after establishing port-forwarding.
          long-summary: Add this argument when launching a web browser manually, or for automated testing.
"""

helps['aks create'] = """
    type: command
    short-summary: (PREVIEW) Create a new managed Kubernetes cluster.
    parameters:
        - name: --generate-ssh-keys
          type: string
          short-summary: Generate SSH public and private key files if missing.
        - name: --service-principal
          type: string
          short-summary: Service principal used for authentication to Azure APIs.
          long-summary:  If not specified, a new service principal is created and cached at
                         {sp_cache} to be used by subsequent `az aks` commands.
        - name: --client-secret
          type: string
          short-summary: Secret associated with the service principal. This argument is required if
                         `--service-principal` is specified.
        - name: --node-vm-size -s
          type: string
          short-summary: Size of Virtual Machines to create as Kubernetes nodes.
        - name: --dns-name-prefix -p
          type: string
          short-summary: Prefix for hostnames that are created. If not specified, generate a hostname using the
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
          short-summary: Version of Kubernetes to use for creating the cluster, such as "1.7.12" or "1.8.7".
          populator-commands:
          - "`az aks get-versions`"
        - name: --ssh-key-value
          type: string
          short-summary: Public key path or key contents to install on node VMs for SSH access. For example,
                         'ssh-rsa AAAAB...snip...UcyupgH azureuser@linuxvm'.
        - name: --admin-username -u
          type: string
          short-summary: User account to create on node VMs for SSH access.
    examples:
        - name: Create a Kubernetes cluster with an existing SSH public key.
          text: az aks create -g MyResourceGroup -n MyManagedCluster --ssh-key-value /path/to/publickey
        - name: Create a Kubernetes cluster with a specific version.
          text: az aks create -g MyResourceGroup -n MyManagedCluster --kubernetes-version 1.8.7
        - name: Create a Kubernetes cluster with a larger node pool.
          text: az aks create -g MyResourceGroup -n MyManagedCluster --node-count 7
""".format(sp_cache=AKS_SERVICE_PRINCIPAL_CACHE)

helps['aks delete'] = """
    type: command
    short-summary: (PREVIEW) Delete a managed Kubernetes cluster.
"""

helps['aks get-credentials'] = """
    type: command
    short-summary: (PREVIEW) Get access credentials for a managed Kubernetes cluster.
    parameters:
        - name: --admin -a
          type: bool
          short-summary: "Get cluster administrator credentials.  Default: cluster user credentials."
        - name: --file -f
          type: string
          short-summary: Kubernetes configuration file to update. Use "-" to print YAML to stdout instead.
"""

helps['aks get-upgrades'] = """
    type: command
    short-summary: (PREVIEW) Get the upgrade versions available for a managed Kubernetes cluster.
"""

helps['aks get-versions'] = """
    type: command
    short-summary: (PREVIEW) Get the versions available for creating a managed Kubernetes cluster.
"""

helps['aks install-cli'] = """
    type: command
    short-summary: (PREVIEW) Download and install kubectl, the Kubernetes command-line tool.
"""

helps['aks install-connector'] = """
    type: command
    short-summary: (PREVIEW) Install the ACI Connector on a managed Kubernetes cluster.
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
          short-summary: Service principal used for authentication to Azure APIs.
          long-summary:  If not specified, use the AKS service principal defined in the file
                         /etc/kubernetes/azure.json on the node which runs the virtual kubelet pod.
        - name: --client-secret
          type: string
          short-summary: Secret associated with the service principal. This argument is required if
                         `--service-principal` is specified.
        - name: --image-tag
          type: string
          short-summary: The image tag of the virtual kubelet. Use 'latest' if it is not specified
        - name: --aci-resource-group
          type: string
          short-summary: The resource group to create the ACI container groups. Use the MC_*
                         resource group if it is not specified.
        - name: --location -l
          type: string
          short-summary: The location to create the ACI container groups. Use the location of the MC_*
                         resource group if it is not specified.
    examples:
        - name: Install the ACI Connector for Linux to a managed Kubernetes cluster.
          text: |-
            az aks install-connector --name MyManagedCluster --resource-group MyResourceGroup \\
              --connector-name aci-connector
        - name: Install the ACI Connector for Windows to a managed Kubernetes cluster.
          text: |-
            az aks install-connector --name MyManagedCluster --resource-group MyResourceGroup \\
               --connector-name aci-connector --os-type Windows
        - name: Install the ACI Connector for both Windows and Linux to a managed Kubernetes cluster.
          text: |-
            az aks install-connector --name MyManagedCluster --resource-group MyResourceGroup \\
              --connector-name aci-connector --os-type Both
        - name: Install the ACI Connector using a specific service principal in a specific resource group.
          text: |-
            az aks install-connector --name MyManagedCluster --resource-group MyResourceGroup \\
              --connector-name aci-connector --service-principal <SPN_ID> --client-secret <SPN_SECRET> \\
              --aci-resource-group <ACI resource group>
        - name: Install the ACI Connector from a custom Helm chart with custom tag.
          text: |-
            az aks install-connector --name MyManagedCluster --resource-group MyResourceGroup \\
              --connector-name aci-connector --chart-url <CustomURL> --image-tag <VirtualKubeletImageTag>
""".format(sp_cache=AKS_SERVICE_PRINCIPAL_CACHE)

helps['aks list'] = """
    type: command
    short-summary: (PREVIEW) List managed Kubernetes clusters.
"""

helps['aks remove-connector'] = """
    type: command
    short-summary: (PREVIEW) Remove the ACI Connector from a managed Kubernetes cluster.
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
        - name: Remove the ACI Connector from a cluster using the graceful mode.
          text: |-
            az aks remove-connector --name MyManagedCluster --resource-group MyResourceGroup \\
              --connector-name MyConnector --graceful
"""

helps['aks scale'] = """
    type: command
    short-summary: (PREVIEW) Scale the node pool in a managed Kubernetes cluster.
    parameters:
        - name: --node-count -c
          type: int
          short-summary: Number of nodes in the Kubernetes node pool.
"""

helps['aks show'] = """
    type: command
    short-summary: (PREVIEW) Show the details for a managed Kubernetes cluster.
"""

helps['aks upgrade'] = """
    type: command
    short-summary: (PREVIEW) Upgrade a managed Kubernetes cluster to a newer version.
    long-summary: "Kubernetes will be unavailable during cluster upgrades."
    parameters:
        - name: --kubernetes-version -k
          type: string
          short-summary: Version of Kubernetes to upgrade the cluster to, such as "1.7.12" or "1.8.7".
          populator-commands:
          - "`az aks get-upgrades`"
"""

helps['aks upgrade-connector'] = """
    type: command
    short-summary: (PREVIEW) Upgrade the ACI Connector on a managed Kubernetes cluster.
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
          short-summary: Service principal used for authentication to Azure APIs.
          long-summary:  If not specified, use the AKS service principal defined in the file
                         /etc/kubernetes/azure.json on the node which runs the virtual kubelet pod.
        - name: --client-secret
          type: string
          short-summary: Secret associated with the service principal. This argument is required if
                         `--service-principal` is specified.
        - name: --image-tag
          type: string
          short-summary: The image tag of the virtual kubelet. Use 'latest' if it is not specified
        - name: --aci-resource-group
          type: string
          short-summary: The resource group to create the ACI container groups. Use the MC_*
                         resource group if it is not specified.
        - name: --location -l
          type: string
          short-summary: The location to create the ACI container groups. Use the location of the MC_*
                         resource group if it is not specified.
    examples:
        - name: Upgrade the ACI Connector for Linux to a managed Kubernetes cluster.
          text: |-
            az aks upgrade-connector --name MyManagedCluster --resource-group MyResourceGroup \\
              --connector-name aci-connector
        - name: Upgrade the ACI Connector for Windows to a managed Kubernetes cluster.
          text: |-
            az aks upgrade-connector --name MyManagedCluster --resource-group MyResourceGroup \\
               --connector-name aci-connector --os-type Windows
        - name: Upgrade the ACI Connector for both Windows and Linux to a managed Kubernetes cluster.
          text: |-
            az aks upgrade-connector --name MyManagedCluster --resource-group MyResourceGroup \\
              --connector-name aci-connector --os-type Both
        - name: Upgrade the ACI Connector to use a specific service principal in a specific resource group.
          text: |-
            az aks upgrade-connector --name MyManagedCluster --resource-group MyResourceGroup \\
              --connector-name aci-connector --service-principal <SPN_ID> --client-secret <SPN_SECRET> \\
              --aci-resource-group <ACI resource group>
        - name: Upgrade the ACI Connector from a custom Helm chart with custom tag.
          text: |-
            az aks upgrade-connector --name MyManagedCluster --resource-group MyResourceGroup \\
              --connector-name aci-connector --chart-url <CustomURL> --image-tag <VirtualKubeletImageTag>
"""

helps['aks use-dev-spaces'] = """
    type: command
    short-summary: (PREVIEW) Use Azure Dev Spaces with a managed Kubernetes cluster.
    parameters:
        - name: --space -s
          type: string
          short-summary: Name of the dev space to use.
        - name: --parent-space -p
          type: string
          short-summary: Name of a parent dev space to inherit from when creating a new dev space. By default, if there is already a single dev space with no parent, the new space inherits from this one.
"""

helps['aks remove-dev-spaces'] = """
    type: command
    short-summary: (PREVIEW) Remove Azure Dev Spaces from a managed Kubernetes cluster.
"""

helps['aks wait'] = """
    type: command
    short-summary: (PREVIEW) Wait for a managed Kubernetes cluster to reach a desired state.
    long-summary: If an operation on a cluster was interrupted or was started with `--no-wait`, use this command to
                  wait for it to complete.
    examples:
        - name: Wait for a cluster to be upgraded, polling every minute for up to thirty minutes.
          text: |-
            az aks wait -g MyResourceGroup -n MyManagedCluster --updated --interval 60 --timeout 1800
"""
