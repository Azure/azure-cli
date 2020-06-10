# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['hdinsight'] = """
type: group
short-summary: Manage HDInsight resources.
"""

helps['hdinsight application'] = """
type: group
short-summary: Manage HDInsight applications.
"""

helps['hdinsight application create'] = """
type: command
short-summary: Create an application for a HDInsight cluster.
examples:
  - name: Create an application with a script URI.
    text: |-
        az hdinsight application create -g MyResourceGroup -n MyApplication \\
        --cluster-name MyCluster \\
        --script-uri https://hdiconfigactions.blob.core.windows.net/linuxhueconfigactionv02/install-hue-uber-v02.sh \\
        --script-action-name MyScriptAction \\
        --script-parameters '"-version latest -port 20000"'
  - name: Create an application with a script URI and specified edge node size.
    text: |-
        az hdinsight application create -g MyResourceGroup -n MyApplication \\
        --cluster-name MyCluster \\
        --script-uri https://hdiconfigactions.blob.core.windows.net/linuxhueconfigactionv02/install-hue-uber-v02.sh \\
        --script-action-name MyScriptAction \\
        --script-parameters "-version latest -port 20000" \\
        --edgenode-size Standard_D4_v2
  - name: Create an application with HTTPS Endpoint.
    text: |-
        az hdinsight application create -g MyResourceGroup -n MyApplication \\
        --cluster-name MyCluster \\
        --script-uri https://hdiconfigactions.blob.core.windows.net/linuxhueconfigactionv02/install-hue-uber-v02.sh \\
        --script-action-name MyScriptAction \\
        --script-parameters "-version latest -port 20000" \\
        --destination-port 8888 \\
        --sub-domain-suffix was
"""

helps['hdinsight application wait'] = """
type: command
short-summary: Place the CLI in a waiting state until an operation is complete.
"""

helps['hdinsight create'] = """
type: command
short-summary: Create a new cluster.
examples:
  - name: Create a cluster with an existing storage account.
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" \\
        --storage-account MyStorageAccount
  - name: Create a cluster with minimal tls version.
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" \\
        --storage-account MyStorageAccount --minimal-tls-version 1.2
  - name: Create a cluster with the Enterprise Security Package (ESP).
    text: |-
        az hdinsight create --esp -t spark -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" \\
        --storage-account MyStorageAccount \\
        --subnet "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/MyRG/providers/Microsoft.Network/virtualNetworks/MyVnet/subnets/subnet1" \\
        --domain "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/MyRG/providers/Microsoft.AAD/domainServices/MyDomain.onmicrosoft.com" \\
        --assign-identity "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/MyMsiRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/MyMSI" \\
        --cluster-admin-account MyAdminAccount@MyDomain.onmicrosoft.com \\
        --cluster-users-group-dns MyGroup
  - name: Create a Kafka cluster with disk encryption. See https://docs.microsoft.com/azure/hdinsight/kafka/apache-kafka-byok.
    text: |-
        az hdinsight create -t kafka -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" --workernode-data-disks-per-node 2 \\
        --storage-account MyStorageAccount \\
        --encryption-key-name kafkaClusterKey \\
        --encryption-key-version 00000000000000000000000000000000 \\
        --encryption-vault-uri https://MyKeyVault.vault.azure.net \\
        --assign-identity MyMSI
  - name: Create a kafka cluster with kafka rest proxy.
    text: |-
        az hdinsight create -t kafka -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" --workernode-data-disks-per-node 2 \\
        --storage-account MyStorageAccount \\
        --kafka-management-node-size "Standard_D4_v2" \\
        --kafka-client-group-id MySecurityGroupId \\
        --kafka-client-group-name MySecurityGroupName
        --component-version kafka=2.1
  - name: Create a cluster with Azure Data Lake Storage Gen2
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" \\
        --storage-account MyStorageAccount \\
        --storage-account-managed-identity MyMSI
  - name: Create a cluster with configuration from JSON string.
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" \\
        --storage-account MyStorageAccount \\
        --cluster-configuration {'gateway':{'restAuthCredential.username':'admin'}}
  - name: Create a cluster with configuration from a local file.
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" \\
        --storage-account MyStorageAccount \\
        --cluster-configuration @config.json
"""

helps['hdinsight list'] = """
type: command
short-summary: List HDInsight clusters in a resource group or subscription.
"""

helps['hdinsight monitor'] = """
type: group
short-summary: Manage Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight monitor disable'] = """
type: command
short-summary: Disable the Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight monitor enable'] = """
type: command
short-summary: Enable the Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight monitor show'] = """
type: command
short-summary: Get the status of Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight rotate-disk-encryption-key'] = """
type: command
short-summary: Rotate the disk encryption key of the specified HDInsight cluster.
"""

helps['hdinsight script-action'] = """
type: group
short-summary: Manage HDInsight script actions.
"""

helps['hdinsight script-action execute'] = """
type: command
short-summary: Execute script actions on the specified HDInsight cluster.
examples:
  - name: Execute a script action and persist on success.
    text: |-
        az hdinsight script-action execute -g MyResourceGroup -n MyScriptActionName \\
        --cluster-name MyCluster \\
        --script-uri https://hdiconfigactions.blob.core.windows.net/linuxgiraphconfigactionv01/giraph-installer-v01.sh \\
        --roles headnode workernode \\
        --persist-on-success
"""

helps['hdinsight wait'] = """
type: command
short-summary: Place the CLI in a waiting state until an operation is complete.
"""
