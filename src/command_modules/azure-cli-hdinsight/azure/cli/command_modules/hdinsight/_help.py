# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from knack.help_files import helps


helps['hdinsight'] = """
    type: group
    short-summary: Manage HDInsight resources.
"""

helps['hdinsight create'] = """
    type: command
    short-summary: Creates a new cluster.
    examples:
        - name: Create a cluster with an existing storage account.
          text: |-
              az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
              -p "HttpPassword1234!" \\
              --storage-account MyStorageAccount
        - name: Create a cluster with Enterprise Security Package.
          text: |-
              az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
              -p "HttpPassword1234!" \\
              --storage-account MyStorageAccount \\
              --subnet "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/MyRG/providers/Microsoft.Network/virtualNetworks/MyVnet/subnets/subnet1" \\
              --domain "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/MyRG/providers/Microsoft.AAD/domainServices/MyDomain.onmicrosoft.com" \\
              --assign-identity "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/MyMsiRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/MyMSI" \\
              --cluster-admin-account MyAdminAccount@MyDomain.onmicrosoft.com
        - name: Create a Kafka cluster with disk encryption. See https://docs.microsoft.com/en-us/azure/hdinsight/kafka/apache-kafka-byok.
          text: |-
             az hdinsight create -t kafka -g MyResourceGroup -n MyCluster \\
             -p "HttpPassword1234!" --workernode-data-disks-per-node 2 \\
             --storage-account MyStorageAccount \\
             --encryption-key-name kafkaClusterKey \\
             --encryption-key-version 00000000000000000000000000000000 \\
             --encryption-vault-uri https://MyKeyVault.vault.azure.net \\
             --assign-identity MyMSI
"""

helps['hdinsight list'] = """
    type: command
    short-summary: List clusters in the resource group or subscription.
"""

helps['hdinsight wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until an operation is complete.
"""

helps['hdinsight rotate-disk-encryption-key'] = """
    type: command
    short-summary: Rotate disk encryption key of the specified HDInsight cluster.
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
              az hdinsight application create -g MyResourceGroup -n MyCluster \\
              --application-name MyApplication \\
              --script-uri https://path/to/install/script.sh \\
              --script-action-name MyScriptAction \\
              --script-parameters '"-option value"'
        - name: Create an application with a script URI and specified edge node size.
          text: |-
              az hdinsight application create -g MyResourceGroup -n MyCluster \\
              --application-name MyApplication \\
              --script-uri https://path/to/install/script.sh \\
              --script-action-name MyScriptAction \\
              --script-parameters '"-option value"' \\
              --edgenode-size Standard_D4_v2
"""

helps['hdinsight application wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until an operation is complete.
"""

helps['hdinsight oms'] = """
    type: group
    short-summary: Manage HDInsight Operations Management Suite (OMS).
"""

helps['hdinsight oms enable'] = """
    type: command
    short-summary: Enables the Operations Management Suite (OMS) on the HDInsight cluster.
"""

helps['hdinsight script-action'] = """
    type: group
    short-summary: Manage HDInsight script actions.
"""

helps['hdinsight script-action execute'] = """
    type: command
    short-summary: Executes script actions on the specified HDInsight cluster.
"""

helps['hdinsight script-action list'] = """
    type: command
    short-summary: Lists script actions for the specified cluster.
    examples:
        - name: Lists all the persisted script actions for the specified cluster.
          text: |-
              az hdinsight script-action list -n MyCluster -g MyResourceGroup --persisted
        - name: Lists all scripts' execution history for the specified cluster.
          text: |-
              az hdinsight script-action list -n MyCluster -g MyResourceGroup
"""
