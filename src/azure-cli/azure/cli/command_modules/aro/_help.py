# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['azure-redhat-openshift'] = """
  type: group
  short-summary: Manage Azure Red Hat OpenShift clusters.
"""

helps['azure-redhat-openshift create'] = """
  type: command
  short-summary: Create a cluster.
  examples:
  - name: Create a cluster.
    text: az azure-redhat-openshift create --resource-group MyResourceGroup --name MyCluster --vnet MyVnet --master-subnet MyMasterSubnet --worker-subnet MyWorkerSubnet
  - name: Create a cluster with 5 compute nodes and Red Hat pull secret.
    text: az azure-redhat-openshift create --resource-group MyResourceGroup --name MyCluster --vnet MyVnet --master-subnet MyMasterSubnet --worker-subnet MyWorkerSubnet --worker-count 5 --pull-secret @pullsecret.txt
  - name: Create a private cluster.
    text: az azure-redhat-openshift create --resource-group MyResourceGroup --name MyCluster --vnet MyVnet --master-subnet MyMasterSubnet --worker-subnet MyWorkerSubnet --apiserver-visibility Private --ingress-visibility Private
"""

helps['azure-redhat-openshift list'] = """
  type: command
  short-summary: List clusters.
  examples:
  - name: List clusters.
    text: az azure-redhat-openshift list
  - name: List clusters with table view.
    text: az azure-redhat-openshift list -o table
"""

helps['azure-redhat-openshift delete'] = """
  type: command
  short-summary: Delete a cluster.
  examples:
  - name: Delete a cluster.
    text: az azure-redhat-openshift delete --name MyCluster --resource-group MyResourceGroup
"""

helps['azure-redhat-openshift show'] = """
  type: command
  short-summary: Get the details of a cluster.
  examples:
  - name: Get the details of a cluster.
    text: az azure-redhat-openshift show --name MyCluster --resource-group MyResourceGroup
"""

helps['azure-redhat-openshift update'] = """
  type: command
  short-summary: Update a cluster.
  examples:
  - name: Update a cluster.
    text: az azure-redhat-openshift update --name MyCluster --resource-group MyResourceGroup
"""

helps['azure-redhat-openshift list-credentials'] = """
  type: command
  short-summary: List credentials of a cluster.
  examples:
  - name: List credentials of a cluster.
    text: az azure-redhat-openshift list-credentials --name MyCluster --resource-group MyResourceGroup
"""

helps['azure-redhat-openshift wait'] = """
  type: command
  short-summary: Wait for a cluster to reach a desired state.
  long-summary: If an operation on a cluster was interrupted or was started with `--no-wait`, use this command to wait for it to complete.
"""
