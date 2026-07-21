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
long-summary: We no longer maintain module before version 2.30.0. It is recommended to upgrade to at least version 2.30.0.
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
  - name: Create a cluster which enables encryption in transit.
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" \\
        --storage-account MyStorageAccount --encryption-in-transit true
  - name: Create a cluster with encryption at host.
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" \\
        --storage-account MyStorageAccount --encryption-at-host true
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
  - name: Create a cluster with the Enterprise Security Package (ESP) and enable HDInsight ID Broker.
    text: |-
        az hdinsight create --esp --idbroker -t spark -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" \\
        --storage-account MyStorageAccount \\
        --subnet "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/MyRG/providers/Microsoft.Network/virtualNetworks/MyVnet/subnets/subnet1" \\
        --domain "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/MyRG/providers/Microsoft.AAD/domainServices/MyDomain.onmicrosoft.com" \\
        --assign-identity "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/MyMsiRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/MyMSI" \\
        --cluster-admin-account MyAdminAccount@MyDomain.onmicrosoft.com \\
        --cluster-users-group-dns MyGroup
  - name: Create a Kafka cluster with disk encryption. See https://learn.microsoft.com/azure/hdinsight/kafka/apache-kafka-byok.
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
  - name: Create a cluster which Load-based Autoscale.
    text: |-
        az hdinsight create -t spark --version 3.6 -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" --storage-account MyStorageAccount \\
        --autoscale-type Load --autoscale-min-workernode-count 3 --autoscale-max-workernode-count 5
  - name: Create a cluster which Schedule-based Autoscale.
    text: |-
        az hdinsight create -t spark --version 3.6 -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" --storage-account MyStorageAccount \\
        --autoscale-type Schedule --timezone "Pacific Standard Time" --days Monday \\
        --time 09:00 --autoscale-workernode-count 5
  - name: Create a cluster with Relay Outbound and Private Link feature.
    text: |-
        az hdinsight create -t spark --version 3.6 -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" --storage-account MyStorageAccount \\
        --subnet "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/fakevnet/subnets/default" \\
        --resource-provider-connection Outbound --enable-private-link
  - name: Create a cluster with Compute Isolation feature.
    text: |-
        az hdinsight create -t spark --version 3.6 -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" --storage-account MyStorageAccount \\
        --enable-compute-isolation --workernode-size "Standard_E8S_V3" --headnode-size "Standard_E8S_V3"
  - name: Create a cluster with WASB + MSI.
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        -p "HttpPassword1234!" \\
        --storage-account MyStorageAccount \\
        --storage-account-managed-identity MyMSI
  - name: Create a entra user cluster with Entra User By objectId or upn (comma-separated)
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        --ssh-password "sshPassword1234!" \\
        --storage-account MyStorageAccount \\
        --entra-user-identity "00000000-0000-0000-0000-000000000000","00000000-0000-0000-0000-000000000000","user@contoso.com"
  - name: Create a entra user cluster with Entra User By objectId or upn (comma-separated, use short name)
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        --ssh-password "sshPassword1234!" \\
        --storage-account MyStorageAccount \\
        --entra-uid "00000000-0000-0000-0000-000000000000","00000000-0000-0000-0000-000000000000","user@contoso.com"
  - name: Create a entra user cluster with Entra User By objectId or upn (space-separated)
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        --ssh-password "sshPassword1234!" \\
        --storage-account MyStorageAccount \\
        --entra-user-identity "00000000-0000-0000-0000-000000000000" "00000000-0000-0000-0000-000000000000" "user@contoso.com"
  - name: Create a entra user cluster with Entra User By a JSON string
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        --ssh-password "sshPassword1234!" \\
        --storage-account MyStorageAccount \\
        --entra-user-full-info '[{\"objectId\": \"00000000-0000-0000-0000-000000000000\",\"displayName\": \"name\",\"upn\": \"user@contoso.com\"}]'
  - name: Create a entra user cluster with Entra User By a JSON string (use short name)
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        --ssh-password "sshPassword1234!" \\
        --storage-account MyStorageAccount \\
        --entra-uinfo '[{\"objectId\": \"00000000-0000-0000-0000-000000000000\",\"displayName\": \"name\",\"upn\": \"user@contoso.com\"}]'
  - name: Create a entra user cluster with Entra User By a JSON file
    text: |-
        az hdinsight create -t spark -g MyResourceGroup -n MyCluster \\
        --ssh-password "sshPassword1234!" \\
        --storage-account MyStorageAccount \\
        --entra-user-full-info @config.json
"""

helps['hdinsight resize'] = """
type: command
short-summary: Resize the specified HDInsight cluster to the specified size.
examples:
  - name: Resize the cluster's workernode.
    text: |-
        az hdinsight resize --name MyCluster --resource-group rg --workernode-count 5
"""

helps['hdinsight update'] = """
type: command
short-summary: Update the tags or identity of the specified HDInsight cluster. Setting the identity property will override the existing identity configuration of the cluster.
examples:
  - name: Update the tags.
    text: |-
        az hdinsight update --name MyCluster --resource-group rg --tags key=value
  - name: Update manage identity with single UserAssigned msi.
    text: |-
        az hdinsight update --name MyCluster --resource-group rg --assign-identity-type UserAssigned --assign-identity MyMsi
  - name: Update manage identity with multiple UserAssigned msi.
    text: |-
        az hdinsight update --name MyCluster --resource-group rg --assign-identity-type UserAssigned --assign-identity MyMsi1 MyMsi2
  - name: Update SystemAssigned manage identity.
    text: |-
        az hdinsight update --name MyCluster --resource-group rg --assign-identity-type SystemAssigned
  - name: Update manage identity with SystemAssigned,UserAssigned msi.
    text: |-
        az hdinsight update --name MyCluster --resource-group rg --assign-identity-type "SystemAssigned,UserAssigned" --assign-identity MyMsi1
"""

helps['hdinsight list'] = """
type: command
short-summary: List HDInsight clusters in a resource group or subscription.
"""

helps['hdinsight monitor'] = """
type: group
short-summary: Manage Classic Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight monitor disable'] = """
type: command
short-summary: Disable the Classic Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight monitor enable'] = """
type: command
short-summary: Enable the Classic Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight monitor show'] = """
type: command
short-summary: Get the status of Classic Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight azure-monitor'] = """
type: group
short-summary: Manage Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight azure-monitor disable'] = """
type: command
short-summary: Disable the Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight azure-monitor enable'] = """
type: command
short-summary: Enable the Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight azure-monitor show'] = """
type: command
short-summary: Get the status of Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight azure-monitor-agent'] = """
type: group
short-summary: Manage Azure Monitor Agent logs integration on an HDInsight cluster.
"""

helps['hdinsight azure-monitor-agent disable'] = """
type: command
short-summary: Disable the Azure Monitor Agent logs integration on an HDInsight cluster.
examples:
  - name: Disable the Azure Monitor Agent logs integration on an HDInsight cluster.
    text: |-
        az hdinsight azure-monitor-agent disable --name MyCluster --resource-group rg
"""

helps['hdinsight azure-monitor-agent enable'] = """
type: command
short-summary: Enable the Azure Monitor Agent logs integration on an HDInsight cluster.
examples:
  - name: Enable the Azure Monitor Agent logs integration on an HDInsight cluster.
    text: |-
        az hdinsight azure-monitor-agent enable --name MyCluster --resource-group rg --workspace WorkspaceId --primary-key WorkspaceKey
"""

helps['hdinsight azure-monitor-agent show'] = """
type: command
short-summary: Get the status of Azure Monitor Agent logs integration on an HDInsight cluster.
examples:
  - name: Get the status of Azure Monitor Agent logs integration on an HDInsight cluster.
    text: |-
        az hdinsight azure-monitor-agent show --name MyCluster --resource-group rg
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

helps['hdinsight host'] = """
type: group
short-summary: Manage HDInsight cluster's virtual hosts.
"""

helps['hdinsight host list'] = """
type: command
short-summary: List the hosts of the specified HDInsight cluster.
examples:
  - name: List the hosts of the specified HDInsight cluster.
    text: |-
        az hdinsight host list --resource-group MyResourceGroup --cluster-name MyCluster
"""

helps['hdinsight host restart'] = """
type: command
short-summary: Restart the specific hosts of the specified HDInsight cluster.
examples:
  - name: Restart the specific hosts of the specified HDInsight cluster.
    text: |-
        az hdinsight host restart --resource-group MyResourceGroup --cluster-name MyCluster --host-names hostname1 hostname2
"""

helps['hdinsight autoscale'] = """
type: group
short-summary: Manage HDInsight cluster's Autoscale configuration.
"""

helps['hdinsight autoscale create'] = """
type: command
short-summary: Enable Autoscale for a running cluster.
examples:
  - name: Enable Load-based Autoscale for a running cluster.
    text: |-
        az hdinsight autoscale create --resource-group MyResourceGroup --cluster-name MyCluster --type Load \\
        --min-workernode-count 3 --max-workernode-count 5
  - name: Enable Schedule-based Autoscale for a running cluster.
    text: |-
        az hdinsight autoscale create --resource-group MyResourceGroup --cluster-name MyCluster --type Schedule \\
        --timezone "Pacific Standard Time" --days Monday Tuesday --time 09:00 --workernode-count 5
"""

helps['hdinsight autoscale update'] = """
type: command
short-summary: Update the Autoscale configuration.
examples:
  - name: Update Load-based Autoscale related configuration.
    text: |-
        az hdinsight autoscale update --resource-group MyResourceGroup --cluster-name MyCluster --max-workernode-count 5
  - name: Update Schedule-based Autoscale related configuration.
    text: |-
        az hdinsight autoscale update --resource-group MyResourceGroup --cluster-name MyCluster --timezone "China Standard Time"
"""

helps['hdinsight autoscale show'] = """
type: command
short-summary: Get the Autoscale configuration of a specified cluster.
examples:
  - name: Get the Autoscale configuration.
    text: |-
        az hdinsight autoscale show --resource-group MyResourceGroup --cluster-name MyCluster
"""

helps['hdinsight autoscale delete'] = """
type: command
short-summary: Disable Autoscale for a running cluster.
examples:
  - name: Disable Autoscale for a running cluster.
    text: |-
        az hdinsight autoscale delete --resource-group MyResourceGroup --cluster-name MyCluster
"""

helps['hdinsight autoscale list-timezones'] = """
type: command
short-summary: List the available timezone name when enabling Schedule-based Autoscale.
examples:
  - name: List the available timezone name.
    text: |-
        az hdinsight autoscale list-timezones
"""

helps['hdinsight autoscale wait'] = """
type: command
short-summary: Place the CLI in a waiting state until an operation is complete.
"""

helps['hdinsight autoscale condition'] = """
type: group
short-summary: Manage schedule condition of the HDInsight cluster which enabled Schedule-based Autoscale.
"""

helps['hdinsight autoscale condition create'] = """
type: command
short-summary: Add a new schedule condition.
examples:
  - name: Add a new schedule condition.
    text: |-
        az hdinsight autoscale condition create --resource-group MyResourceGroup --cluster-name MyCluster \\
        --days Monday Tuesday --time 09:00 --workernode-count 5
"""

helps['hdinsight autoscale condition update'] = """
type: command
short-summary: Update a schedule condition.
examples:
  - name: Update a schedule condition.
    text: |-
        az hdinsight autoscale condition update --resource-group MyResourceGroup --cluster-name MyCluster --index 0 \\
        --time 10:00 --workernode-count 5
"""

helps['hdinsight autoscale condition list'] = """
type: command
short-summary: List all schedule conditions.
examples:
  - name: List all schedule conditions.
    text: |-
        az hdinsight autoscale condition list --resource-group MyResourceGroup --cluster-name MyCluster
"""

helps['hdinsight autoscale condition delete'] = """
type: command
short-summary: Delete schedule condition.
examples:
  - name: Delete a schedule condition.
    text: |-
        az hdinsight autoscale condition delete --resource-group MyResourceGroup --cluster-name MyCluster --index 0
  - name: Delete multiple schedule conditions.
    text: |-
        az hdinsight autoscale condition delete --resource-group MyResourceGroup --cluster-name MyCluster --index 0 1
"""

helps['hdinsight autoscale condition wait'] = """
type: command
short-summary: Place the CLI in a waiting state until an operation is complete.
"""

helps['hdinsight wait'] = """
type: command
short-summary: Place the CLI in a waiting state until an operation is complete.
"""

helps['hdinsight autoscale wait'] = """
type: command
short-summary: Place the CLI in a waiting state until an operation is complete.
"""

helps['hdinsight credentials'] = """
type: group
short-summary: Manage credentials for an existing HDInsight cluster, including Entra ID users and HTTP password.
"""

helps['hdinsight credentials update'] = """
type: command
short-summary: Update credentials for an existing HDInsight cluster, including Entra ID users and HTTP password.
examples:
  - name: Update Entra ID users by objectId or upn (comma-separated)
    text: |-
        az hdinsight credentials update --name MyCluster --resource-group rg \\
        --entra-user-identity "00000000-0000-0000-0000-000000000000","00000000-0000-0000-0000-000000000000","user@contoso.com"
  - name: Update Entra ID users by objectId or upn (comma-separated, use short name)
    text: |-
        az hdinsight credentials update --name MyCluster --resource-group rg \\
        --entra-uid "00000000-0000-0000-0000-000000000000","00000000-0000-0000-0000-000000000000","user@contoso.com"
  - name: Update Entra ID users by objectId or upn (space-separated)
    text: |-
        az hdinsight credentials update --name MyCluster --resource-group rg \\
        --entra-user-identity "00000000-0000-0000-0000-000000000000","00000000-0000-0000-0000-000000000000","user@contoso.com"
  - name: Update Entra ID users using a JSON string
    text: |-
        az hdinsight credentials update --name MyCluster --resource-group rg \\
        --entra-user-full-info '[{\"objectId\": \"00000000-0000-0000-0000-000000000000\",\"displayName\": \"name\",\"upn\": \"user@contoso.com\"}]'
  - name: Update Entra ID users using a JSON string (use short name)
    text: |-
        az hdinsight credentials update --name MyCluster --resource-group rg \\
        --entra-uinfo '[{\"objectId\": \"00000000-0000-0000-0000-000000000000\",\"displayName\": \"name\",\"upn\": \"user@contoso.com\"}]'
  - name: Update Entra ID users using a JSON file
    text: |-
        az hdinsight credentials update --name MyCluster --resource-group rg \\
        --entra-user-full-info @config.json
  - name: Update the HTTP password for the cluster
    text: |-
        az hdinsight credentials update --name MyCluster --resource-group rg \\
        --http-password "HttpPassword1234!"
"""

helps['hdinsight credentials show'] = """
type: command
short-summary: Show credential configuration of an existing HDInsight cluster, including HTTP username, password, and Entra ID user settings
"""

helps['hdinsight credentials wait'] = """
type: command
short-summary: Place the CLI in a waiting state until an operation is complete.
"""
