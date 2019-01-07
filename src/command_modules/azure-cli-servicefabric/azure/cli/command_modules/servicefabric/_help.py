# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import

# pylint: disable=line-too-long

helps["sf"] = """
     type: group
     short-summary: Manage and administer Azure Service Fabric clusters.
"""

helps["sf application"] = """
    type: group
    short-summary: Manage applications running on an Azure Service Fabric cluster.
"""

helps["sf cluster"] = """
    type: group
    short-summary: Manage an Azure Service Fabric cluster.
"""

helps["sf cluster certificate"] = """
    type: group
    short-summary: Manage a cluster certificate.
"""

helps["sf cluster client-certificate"] = """
    type: group
    short-summary: Manage the client certificate of a cluster.
"""

helps["sf cluster durability"] = """
    type: group
    short-summary: Manage the durability of a cluster.
"""

helps["sf cluster node"] = """
    type: group
    short-summary: Manage the node instance of a cluster.
"""

helps["sf cluster node-type"] = """
    type: group
    short-summary: Manage the node-type of a cluster.
"""

helps["sf cluster reliability"] = """
    type: group
    short-summary: Manage the reliability of a cluster.
"""

helps["sf cluster setting"] = """
    type: group
    short-summary: Manage a cluster's settings.
"""

helps["sf cluster upgrade-type"] = """
    type: group
    short-summary: Manage the upgrade type of a cluster.
"""

helps["sf application certificate"] = """
    type: group
    short-summary: Manage the certificate of an application.
"""

helps["sf cluster list"] = """
    type: command
    short-summary: List cluster resources.
"""

helps["sf cluster create"] = """
    type: command
    short-summary: Create a new Azure Service Fabric cluster.
    examples:
        - name: Create a cluster with a given size and self-signed certificate that is downloaded locally.
          text: >
            az sf cluster create -g group-name -n cluster1 -l westus --cluster-size 4 --vm-password Password#1234 --certificate-output-folder MyCertificates --certificate-subject-name cluster1
        - name: Use a keyvault certificate and custom template to deploy a cluster.
          text: >
            az sf cluster create -g group-name -n cluster1 -l westus --template-file template.json \\
                --parameter-file parameter.json --secret-identifier https://{KeyVault}.vault.azure.net:443/secrets/{MyCertificate}

"""

helps["sf cluster certificate add"] = """
    type: command
    short-summary: Add a secondary cluster certificate to the cluster.
    examples:
        - name: Add a certificate to a  cluster using a keyvault secret identifier.
          text: |
            az sf cluster certificate add -g group-name -n cluster1 \\
                --secret-identifier 'https://{KeyVault}.vault.azure.net/secrets/{Secret}
        - name: Add a self-signed certificate to a cluster.
          text: >
             az sf cluster certificate add -g group-name -n cluster1 --certificate-subject-name test.com

"""

helps["sf cluster certificate remove"] = """
    type: command
    short-summary: Remove a certificate from a cluster.
    examples:
        - name: Remove a certificate by thumbprint.
          text: >
            az sf cluster certificate remove -g group-name -n cluster1 --thumbprint '5F3660C715EBBDA31DB1FFDCF508302348DE8E7A'

"""

helps["sf cluster client-certificate add"] = """
    type: command
    short-summary: Add a common name or certificate thumbprint to the cluster for client authentication.
    examples:
        - name: Add client certificate by thumbprint
          text: >
            az sf cluster client-certificate add -g group-name -n cluster1 --thumbprint '5F3660C715EBBDA31DB1FFDCF508302348DE8E7A'

"""

helps["sf cluster client-certificate remove"] = """
    type: command
    short-summary: Remove client certificates or subject names used for authentication.
    examples:
        - name: Remove a client certificate by thumbprint.
          text: >
            az sf cluster client-certificate remove -g group-name -n cluster1 --thumbprint '5F3660C715EBBDA31DB1FFDCF508302348DE8E7A'

"""

helps["sf cluster setting set"] = """
    type: command
    short-summary: Update the settings of a cluster.
    examples:
        - name: Set the `MaxFileOperationTimeout` setting for a cluster to 5 seconds.
          text: >
            az sf cluster setting set -g group-name -n cluster1 --section 'NamingService' --parameter 'MaxFileOperationTimeout' --value 5000

"""

helps["sf cluster setting remove"] = """
    type: command
    short-summary: Remove settings from a cluster.
    examples:
        - name: Remove the `MaxFileOperationTimeout` setting from a cluster.
          text: >
            az sf cluster setting remove -g group-name -n cluster1 --section 'NamingService' --parameter 'MaxFileOperationTimeout'

"""

helps["sf cluster reliability update"] = """
    type: command
    short-summary: Update the reliability tier for the primary node in a cluster.
    examples:
        - name: Change the cluster reliability level to 'Silver'.
          text: >
            az sf cluster reliability update -g group-name -n cluster1 --reliability-level Silver

"""

helps["sf cluster durability update"] = """
    type: command
    short-summary: Update the durability tier or VM SKU of a node type in the cluster.
    examples:
        - name: Change the cluster durability level to 'Silver'.
          text: >
            az sf cluster durability update -g group-name -n cluster1 --durability-level Silver

"""

helps["sf cluster node-type add"] = """
    type: command
    short-summary: Add a new node type to a cluster.
    examples:
        - name: Add a new node type to a cluster.
          text: >
            az sf cluster node-type add -g group-name -n cluster1 --node-type 'n2' --capacity 5 --vm-user-name 'adminName' --vm-password User@1234567890

"""

helps["sf cluster node add"] = """
    type: command
    short-summary: Add nodes to a node type in a cluster.
    examples:
        - name: Add 2 'nt1' nodes to a cluster.
          text: >
            az sf cluster node add -g group-name -n cluster1 --number-of-nodes-to-add 2 --node-type 'nt1'

"""

helps["sf cluster node remove"] = """
    type: command
    short-summary: Remove nodes from a node type in a cluster.
    examples:
        - name: Remove 2 'nt1' nodes from a cluster.
          text: >
            az sf cluster node remove -g group-name -n cluster1 --node-type 'nt1' --number-of-nodes-to-remove 2

"""

helps["sf cluster upgrade-type set"] = """
    type: command
    short-summary: Change the  upgrade type for a cluster.
    examples:
        - name: Set a cluster to use the 'Automatic' upgrade mode.
          text: >
            az sf cluster upgrade-type set -g group-name -n cluster1 --upgrade-mode Automatic
"""

helps["sf application certificate add"] = """
    type: command
    short-summary: Add a new certificate to the Virtual Machine Scale Sets that make up the cluster to be used by hosted applications.
    examples:
        - name: Add an application certificate.
          text: >
            az sf application certificate add -g group-name -n cluster1  --secret-identifier 'https://{KeyVault}.vault.azure.net/secrets/{Secret}'
"""
