# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['acs'] = """
     type: group
     short-summary: Manage Azure container services.
"""
helps['acs dcos'] = """
    type: group
    short-summary: Manage a DCOS orchestrated Azure container service.
"""
helps['acs kubernetes'] = """
    type: group
    short-summary: Manage a Kubernetes orchestrated Azure Container service.
"""
helps['acs kubernetes get-credentials'] = """
    type: command
    short-summary: Download and install credentials to access your cluster.
"""
helps['acs scale'] = """
    type: command
    short-summary: Change the private agent count of a container service.
"""
helps['acs install-cli'] = """
    type: command
    short-summary: Download the DCOS/Kubernetes command line.
"""
helps['acs create'] = """
    examples:
        - name: Create a default acs cluster
          text: az acs create -g MyResourceGroup -n MyContainerService
        - name: Create a Kubernetes cluster
          text: az acs create --orchestrator-type Kubernetes -g MyResourceGroup -n MyContainerService
        - name: Create a Kubernetes cluster with ssh key provided
          text: az acs create --orchestrator-type Kubernetes -g MyResourceGroup -n MyContainerService --ssh-key-value MySSHKeyValueOrPath
        - name: Create a acs cluster with two agent pools
          text: az acs create -g MyResourceGroup -n MyContainerService --agent-profiles "[{'name':'agentpool1'},{'name':'agentpool2'}]"
        - name: Create a acs cluster with the second agent pool with vmSize specified
          text: az acs create -g MyResourceGroup -n MyContainerService --agent-profiles "[{'name':'agentpool1'},{'name':'agentpool2','vmSize':'Standard_D2'}]"
"""
