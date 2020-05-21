# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['aro'] = """
    type: group
    short-summary: Manage Azure Red Hat OpenShift clusters.
"""

helps['aro create'] = """
    type: command
    short-summary: Create a cluster.
    examples:
      - name: Create an OpenShift cluster
        text: az aro create --resource-group MyResourceGroup --name MyCluster  --vnet MyVnet --master-subnet MyMasterSubnet --worker-subnet MyWorkerSubnet
      - name: Create an OpenShift cluster with 5 compute nodes and Red Hat Pull Secret
        text: az aro create --resource-group MyResourceGroup --name MyCluster --vnet MyVnet --master-subnet MyMasterSubnet --worker-subnet MyWorkerSubnet --worker-count 5 --pull-secret @pullsecret.txt
"""

helps['aro list'] = """
    type: command
    short-summary: List clusters.
    examples:
      - name: List OpenShift clusters
        text: az aro list
      - name: List OpenShift clusters with table view
        text: az aro list -o table
"""

helps['aro delete'] = """
    type: command
    short-summary: Delete a cluster.
    examples:
      - name: Delete a OpenShift cluster
        text: az aro delete --name MyCluster --resource-group MyResourceGroup
"""

helps['aro show'] = """
    type: command
    short-summary: Get the details of a cluster.
    examples:
      - name: Get the details of a Managed OpenShift cluster
        text: az aro show --name MyCluster --resource-group MyResourceGroup
"""

helps['aro update'] = """
    type: command
    short-summary: Update a cluster.
    examples:
      - name: Update an existing cluster
        text: az aro update --name MyCluster --resource-group MyResourceGroup
"""

helps['aro list-credentials'] = """
    type: command
    short-summary: List credentials of a cluster.
    examples:
      - name: List credentials of a cluster
        text: az aro list-credentials --name MyCluster --resource-group MyResourceGroup
"""

helps['aro wait'] = """
    type: command
    short-summary: Wait for a cluster to reach a desired state.
    long-summary: If an operation on a cluster was interrupted or was started with `--no-wait`, use this command to wait for it to complete.
"""
