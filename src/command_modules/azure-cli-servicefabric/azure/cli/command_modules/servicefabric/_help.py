# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps  # pylint: disable=unused-import

# pylint: disable=line-too-long

helps["sf cluster certificate"] = """
    type: group
    short-summary: Manage the cluster certificate
"""

helps["sf cluster client-certificate"] = """
    type: group
    short-summary: Manage the client certificate of a cluster
"""

helps["sf cluster durability"] = """
    type: group
    short-summary: Manage the durability of a cluster
"""

helps["sf cluster node"] = """
    type: group
    short-summary: Manage the node instance of a cluster
"""

helps["sf cluster node-type"] = """
    type: group
    short-summary: Manage the node-type of a cluster
"""

helps["sf cluster reliability"] = """
    type: group
    short-summary: Manage the reliability of a cluster
"""

helps["sf cluster setting"] = """
    type: group
    short-summary: Manage the cluster setting
"""

helps["sf cluster upgrade-type"] = """
    type: group
    short-summary: Manage the upgrade type of the cluster
"""

helps["sf application certificate"] = """
    type: group
    short-summary: Manage the certificate of the application
"""

helps["sf cluster list"] = """
    type: command
    short-summary: List all the cluster resource in the same subscription
"""

helps["sf cluster create"] = """
    type: command
    short-summary: Create a new Service Fabric cluster
    long-summary: >
        This command uses certificates that you provide or system generated self-signed certificates to set up a new service fabric cluster.
        It can use a default template or a custom template that you provide.
        You have the option of specifying a folder to export the self-signed certificates to or fetching them later from the key vault.
    examples:
        - name: Specify only the cluster size, the cert subject name, and the OS to deploy a cluster
          text: >
            az sf cluster create -g group-name -n cluster1 -l westus -size 4 --vm-password Password#1234 --certificate-output-folder c:\\Mycertificates
        - name: Specify an existing Certificate resource in a key vault and a custom template to deploy a cluster
          text: >
            az sf cluster create -g group-name -n cluster1 -l westus --template-file c:\\template.json --parameter-file c:\\parameter.json
            --secret-identifier https://kv.vault.azure.net:443/secrets/testcertificate/56ec774dc61a462bbc645ffc9b4b225f

"""

helps["sf cluster certificate add"] = """
    type: command
    short-summary: Add a secondary cluster certificate to the cluster.
    examples:
        - name: Add cluster certificate using secret identifier
          text: >
            az sf cluster certificate add -g group-name -n cluster1 --secret-identifier 'https://contoso03vault.vault.azure.net/secrets/contoso03vaultrg/7f7de9131c034172b9df37ccc549524f'
        - name: Add cluster certificate with self-signed certificate
          text: >
             az sf cluster certificate add -g group-name -n cluster1 --certificate-subject-name test.com

"""

helps["sf cluster certificate remove"] = """
    type: command
    short-summary: Remove a cluster certificate from being used for cluster security.
    examples:
        - name: Remove certificate by thumbprint
          text: >
            az sf cluster certificate remove -g group-name -n cluster1 --thumbprint '5F3660C715EBBDA31DB1FFDCF508302348DE8E7A'

"""

helps["sf cluster client-certificate add"] = """
    type: command
    short-summary: Add common name or thumbprint to the cluster for client authentication purposes.
    long-summary: >
            Use this command to add a common name and issuer thumbprint or certificate thumbprint to the cluster,
            so the client can use it for authentication.
    examples:
        - name: Add client certificate by thumbprint
          text: >
            az sf cluster client certificate add -g group-name -n cluster1 --thumbprint '5F3660C715EBBDA31DB1FFDCF508302348DE8E7A'

"""

helps["sf cluster client-certificate remove"] = """
    type: command
    short-summary: Remove a client certificate(s) or certificate subject(s) name(s) from being used for client authentication to the cluster.
    examples:
        - name: Remove client certificate
          text: >
            az sf cluster client certificate remove -g group-name -n cluster1 --thumbprint '5F3660C715EBBDA31DB1FFDCF508302348DE8E7A'

"""

helps["sf cluster setting set"] = """
    type: command
    short-summary: Add or update one or multiple Service Fabric settings to the cluster.
    examples:
        - name: Set cluster setting
          text: >
            az sf cluster setting set -g group-name -n cluster1 --section 'NamingService' --parameter 'MaxFileOperationTimeout' --value 5000

"""

helps["sf cluster setting remove"] = """
    type: command
    short-summary: Remove one or multiple Service Fabric setting from the cluster.
    examples:
        - name: Remove cluster setting
          text: >
            az sf cluster setting remove -g group-name -n cluster1 --section 'NamingService' --parameter 'MaxFileOperationTimeout'

"""

helps["sf cluster reliability update"] = """
    type: command
    short-summary: Update the reliability tier of the primary node type in a cluster.
    examples:
        - name: Change cluster reliability
          text: >
            az sf cluster reliability update -g group-name -n cluster1 --reliability-level Silver

"""

helps["sf cluster durability update"] = """
    type: command
    short-summary: Update the durability tier or VmSku of a node type in the cluster.
    examples:
        - name: Update cluster durability
          text: >
            az sf cluster durability update -g group-name -n cluster1 --durability-level Silver

"""

helps["sf cluster node-type add"] = """
    type: command
    short-summary: Add a new node type to the existing cluster.
    examples:
        - name: Add a new node type for the cluster
          text: >
            az sf cluster node-type add -g group-name -n cluster1 --node-type 'n2' --capacity 5 --vm-user-name 'adminName' --vm-password User@1234567890

"""

helps["sf cluster node add"] = """
    type: command
    short-summary: Add nodes to the specific node type in the cluster.
    examples:
        - name: Add nodes to the cluster
          text: >
            az sf cluster node add -g group-name -n cluster1 --number-of-nodes-to-add 2 --node-type 'nt1'

"""

helps["sf cluster node remove"] = """
    type: command
    short-summary: Remove nodes from the specific node type from a cluster.
    examples:
        - name: Example1
          text: >
            az sf cluster node remove -g group-name -n cluster1 --node-type 'nt1' --number-of-nodes-to-remove 2

"""

helps["sf cluster upgrade-type set"] = """
    type: command
    short-summary: Change the Service Fabric upgrade type of the cluster.
    examples:
        - name: Example1
          text: >
            az sf cluster upgrade-type set -g group-name -n cluster1 --upgrade-mode Automatic

"""

helps["sf application certificate add"] = """
    type: command
    short-summary: Add a new certificate to the Virtual Machine Scale Set(s) that make up the cluster. The certificate is intended to be used as an application certificate.
    examples:
        - name: Add application certificate
          text: >
            az sf cluster application certificate add -g group-name -n cluster1  --secret-identifier 'https://contoso03vault.vault.azure.net/secrets/contoso03vaultrg/7f7de9131c034172b9df37ccc549524f'

"""
