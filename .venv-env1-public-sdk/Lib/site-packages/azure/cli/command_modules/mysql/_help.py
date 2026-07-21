# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['mysql flexible-server'] = """
type: group
short-summary: Manage Azure Database for MySQL Flexible Servers.
"""

helps['mysql flexible-server advanced-threat-protection-setting'] = """
type: group
short-summary: Manage the server's advanced threat protection setting.
"""

helps['mysql flexible-server advanced-threat-protection-setting show'] = """
type: command
short-summary: Get the server's advanced threat protection setting.
examples:
  - name: Get the advanced threat protection setting.
    text: az mysql flexible-server advanced-threat-protection-setting show -g mygroup -n myserver
"""

helps['mysql flexible-server advanced-threat-protection-setting update'] = """
type: command
short-summary: Update the server's advanced threat protection setting.
parameters:
  - name: --state
    type: string
    short-summary: 'State of the advanced threat protection setting'
examples:
  - name: Enable the advanced threat protection setting.
    text: az mysql flexible-server advanced-threat-protection-setting update -g mygroup -n myserver --state Enabled
  - name: Disable the advanced threat protection setting.
    text: az mysql flexible-server advanced-threat-protection-setting update -g mygroup -n myserver --state Disabled
"""

helps['mysql flexible-server create'] = """
type: command
short-summary: Create a MySQL flexible server.
long-summary: >
    Create a MySQL flexible server with custom or default configuration. For more information for network configuration, see

    - Configure public access

    https://learn.microsoft.com/en-us/azure/mysql/flexible-server/how-to-manage-firewall-cli

    - Configure private access

    https://learn.microsoft.com/en-us/azure/mysql/flexible-server/how-to-manage-virtual-network-cli

examples:
  - name: >
      Create a MySQL flexible server with custom parameters
    text: >
        az mysql flexible-server create --location northeurope --resource-group testGroup \\
          --name testserver --admin-user username --admin-password password \\
          --sku-name Standard_B1ms --tier Burstable --public-access 0.0.0.0 --storage-size 32 \\
          --tags "key=value" --version 5.7 --high-availability ZoneRedundant --zone 1 \\
          --standby-zone 3 --storage-auto-grow Enabled --iops 500
  - name: >
      Create a MySQL flexible server with default parameters and public access enabled by default. \
      Resource group, server name, username, password, and default database will be created by CLI
    text: >
        az mysql flexible-server create
  - name: >
      Create a MySQL flexible server with public access and add the range of IP address to have access to this server.
      The --public-access parameter can be 'All', 'None', <startIpAddress>, or <startIpAddress>-<endIpAddress>
    text: >
      az mysql flexible-server create --resource-group testGroup --name testserver --public-access 125.23.54.31-125.23.54.35
  - name: >
      Create a MySQL flexible server with private access. If provided virtual network and subnet do not exists, virtual network and subnet with the specified address prefixes will be created.
    text: >
      az mysql flexible-server create --resource-group testGroup --name testserver --vnet myVnet --subnet mySubnet --address-prefixes 10.0.0.0/16 --subnet-prefixes 10.0.0.0/24
  - name: >
      Create a MySQL flexible server using a new subnet resource ID and new private DNS zone resource ID. The subnet and DNS zone can be created in different subscription or resource group.
    text: |
      az mysql flexible-server create \\
        --resource-group testGroup --name testserver \\
        --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNetName}/subnets/{SubnetName} \\
        --private-dns-zone /subscriptions/{SubID}/resourceGroups/{resourceGroup}/providers/Microsoft.Network/privateDnsZones/testMySQLFlexibleDnsZone.private.mysql.database.azure.com \\
        --address-prefixes 172.0.0.0/16 --subnet-prefixes 172.0.0.0/24
  - name: >
      Create a MySQL flexible server using existing network resources in the same resource group.
      The provided subnet should not have any other resource deployed in it and this subnet will be delegated to Microsoft.DBforMySQL/flexibleServers, if not already delegated.
      The private DNS zone will be linked to the virtual network if not already linked.
    text: >
      # create vnet

      az network vnet create --resource-group testGroup --name testVnet --location testLocation --address-prefixes 172.0.0.0/16


      # create subnet

      az network vnet subnet create --resource-group testGroup --vnet-name testVnet --address-prefixes 172.0.0.0/24 --name testSubnet


      # create private dns zone

      az network private-dns zone create -g testGroup -n testDNS.private.mysql.database.azure.com


      az mysql flexible-server create --resource-group testGroup \\
        --name testserver --location testLocation \\
        --subnet /subscriptions/{SubId}/resourceGroups/{testGroup}/providers/Microsoft.Network/virtualNetworks/tesetVnet/subnets/testSubnet \\
        --private-dns-zone /subscriptions/{SubId}/resourceGroups/{testGroup}/providers/Microsoft.Network/privateDnsZones/testDNS.mysql.database.azure.com\\


      az mysql flexible-server create --resource-group testGroup --name testserver \\
        --vnet testVnet --subnet testSubnet --location testLocation \\
        --private-dns-zone /subscriptions/{SubId}/resourceGroups/{testGroup}/providers/Microsoft.Network/privateDnsZones/testDNS.mysql.database.azure.com
  - name: >
      Create a MySQL flexible server using existing network resources in the different resource group / subscription.
    text: >
      az mysql flexible-server create --resource-group testGroup \\
         --name testserver --location testLocation \\
        --subnet /subscriptions/{SubId2}/resourceGroups/{testGroup2}/providers/Microsoft.Network/virtualNetworks/tesetVnet/subnets/testSubnet \\
        --private-dns-zone /subscriptions/{SubId2}/resourceGroups/{testGroup2}/providers/Microsoft.Network/privateDnsZones/testDNS.mysql.database.azure.com
  - name: >
      Create a MySQL flexible server with data encryption.
    text: >
      # create keyvault

      az keyvault create -g testGroup -n testVault --location testLocation \\
        --enable-purge-protection true


      # create key in keyvault and save its key identifier

      keyIdentifier=$(az keyvault key create --name testKey -p software \\
        --vault-name testVault --query key.kid -o tsv)


      # create identity and save its principalId

      identityPrincipalId=$(az identity create -g testGroup --name testIdentity \\
        --location testLocation --query principalId -o tsv)


      # add testIdentity as an access policy with key permissions 'Wrap Key', 'Unwrap Key', 'Get' and 'List' inside testVault

      az keyvault set-policy -g testGroup -n testVault --object-id $identityPrincipalId \\
        --key-permissions wrapKey unwrapKey get list


      # create flexible server with data encryption enabled

      az mysql flexible-server create -g testGroup -n testServer --location testLocation \\
        --key $keyIdentifier --identity testIdentity
  - name: >
      Create a MySQL flexible server with geo redundant backup and data encryption.
    text: >
      # create keyvault

      az keyvault create -g testGroup -n testVault --location testLocation \\
        --enable-purge-protection true


      # create key in keyvault and save its key identifier

      keyIdentifier=$(az keyvault key create --name testKey -p software \\
        --vault-name testVault --query key.kid -o tsv)


      # create identity and save its principalId

      identityPrincipalId=$(az identity create -g testGroup --name testIdentity \\
        --location testLocation --query principalId -o tsv)


      # add testIdentity as an access policy with key permissions 'Wrap Key', 'Unwrap Key', 'Get' and 'List' inside testVault

      az keyvault set-policy -g testGroup -n testVault --object-id $identityPrincipalId \\
        --key-permissions wrapKey unwrapKey get list


      # create backup keyvault

      az keyvault create -g testGroup -n testBackupVault --location testBackupLocation \\
        --enable-purge-protection true


      # create backup key in backup keyvault and save its key identifier

      backupKeyIdentifier=$(az keyvault key create --name testBackupKey -p software \\
        --vault-name testBackupVault --query key.kid -o tsv)


      # create backup identity and save its principalId

      backupIdentityPrincipalId=$(az identity create -g testGroup --name testBackupIdentity \\
        --location testBackupLocation --query principalId -o tsv)


      # add testBackupIdentity as an access policy with key permissions 'Wrap Key', 'Unwrap Key', 'Get' and 'List' inside testBackupVault

      az keyvault set-policy -g testGroup -n testBackupVault \\
        --object-id $backupIdentityPrincipalId --key-permissions wrapKey unwrapKey get list


      # create flexible server with geo redundant backup and data encryption enabled

      az mysql flexible-server create -g testGroup -n testServer --location testLocation \\
        --geo-redundant-backup Enabled \\
        --key $keyIdentifier --identity testIdentity \\
        --backup-key $backupKeyIdentifier --backup-identity testBackupIdentity
"""

helps['mysql flexible-server import'] = """
type: group
short-summary: Manage import workflows for MySQL Flexible Servers.
"""

helps['mysql flexible-server import create'] = """
type: command
short-summary: Create a new import workflow for flexible server.
long-summary: >
    This command is used for following two purposes:

    To Migrate an external MySQL server to Azure MySQL Flexible server whose backup is stored on an Azure Blob Container.

    To Migrate a Azure MySQL single server to Azure MySQL Flexible server. For more information for network configuration, see

    - Migrate Azure Database for MySQL - Single Server to Flexible Server using Azure Database for MySQL Import CLI

    https://learn.microsoft.com/en-us/azure/mysql/migrate/migrate-single-flexible-mysql-import-cli

    - Configure public access

    https://learn.microsoft.com/en-us/azure/mysql/flexible-server/how-to-manage-firewall-cli

    - Configure private access

    https://learn.microsoft.com/en-us/azure/mysql/flexible-server/how-to-manage-virtual-network-cli

examples:
  - name: >
      Trigger an Import from azure mysql single server.
    text: >
        az mysql flexible-server import create --data-source-type mysql_single \\
          --data-source test-single-server --resource-group test-rg \\
          --location northeurope --name testserver \\
          --sku-name Standard_B1ms --tier Burstable --public-access 0.0.0.0 \\
          --storage-size 32 --tags "key=value" --version 5.7 --high-availability ZoneRedundant \\
          --zone 1 --standby-zone 3 --storage-auto-grow Enabled --iops 500
  - name: >
      Trigger an Online Import from azure mysql single server.
    text: >
        az mysql flexible-server import create --data-source-type mysql_single \\
          --data-source test-single-server --mode "Online" --resource-group test-rg \\
          --location northeurope --name testserver \\
          --sku-name Standard_B1ms --tier Burstable --public-access 0.0.0.0 \\
          --storage-size 32 --tags "key=value" --version 5.7 --high-availability ZoneRedundant \\
          --zone 1 --standby-zone 3 --storage-auto-grow Enabled --iops 500
  - name: >
      Trigger a Import from source backup stored in azure blob container.
    text: >
        az mysql flexible-server import create --data-source-type "azure_blob" \\
          --data-source "https://teststorage.blob.windows.net/backupcontainer" \\
          --resource-group test-rg --name testserver --version 5.7 --location northeurope \\
          --admin-user "username" --admin-password "password" \\
          --sku-name Standard_D2ds_v4 --tier GeneralPurpose --public-access 0.0.0.0 \\
          --storage-size 32 --tags "key=value" --high-availability ZoneRedundant \\
          --zone 1 --standby-zone 3 --storage-auto-grow Enabled --iops 500
  - name: >
      Trigger import from source backup stored in azure blob container. (Backup files not present in container root. Instead present in backupdata/data/)
    text: >
        az mysql flexible-server import create --data-source-type "azure_blob" \\
          --data-source "https://teststorage.blob.windows.net/backupcontainer" \\
          --data-source-backup-dir "backupdata/data/" \\
          --resource-group test-rg --name testserver --version 5.7 --location northeurope \\
          --admin-user "username" --admin-password "password" \\
          --sku-name Standard_D2ds_v4 --tier GeneralPurpose --public-access 0.0.0.0 \\
          --storage-size 32 --tags "key=value" --high-availability ZoneRedundant \\
          --zone 1 --standby-zone 3 --storage-auto-grow Enabled --iops 500
  - name: >
      Trigger import from source backup stored in azure blob container.
      (Backup files present in container root and blob storage accessible through sas token with Read and List permissions. Please pass '--%' in the command with SAS token.)
    text: >
        az mysql flexible-server import create --data-source-type "azure_blob" \\
          --data-source "https://teststorage.blob.windows.net/backupcontainer" \\
          --data-source-sas-token "sp=r&st=2023-07-20T10:30:07Z..."  \\
          --resource-group test-rg --name testserver --version 5.7 --location northeurope \\
          --admin-user "username" --admin-password "password" \\
          --sku-name Standard_D2ds_v4 --tier GeneralPurpose --public-access 0.0.0.0 \\
          --storage-size 32 --tags "key=value" --high-availability ZoneRedundant \\
          --zone 1 --standby-zone 3 --storage-auto-grow Enabled --iops 500
"""

helps['mysql flexible-server import stop-replication'] = """
type: command
short-summary: To stop replication between the source single server and target flexible server.
examples:
  - name: Stop replication to 'testFlexServer'.
    text: az mysql flexible-server import stop-replication -g testGroup -n testFlexServer
"""

helps['mysql flexible-server show'] = """
type: command
short-summary: Get the details of a flexible server.
examples:
  - name: Get the details of a flexible server
    text: az mysql flexible-server show --resource-group testGroup --name testserver
    crafted: true
"""

helps['mysql flexible-server list'] = """
type: command
short-summary: List available flexible servers.
examples:
  - name: List all MySQL flexible servers in a subscription.
    text: az mysql flexible-server list
  - name: List all MySQL flexible servers in a resource group.
    text: az mysql flexible-server list --resource-group testGroup
  - name: List all MySQL flexible servers in a resource group in table format.
    text: az mysql flexible-server list --resource-group testGroup --output table
"""

helps['mysql flexible-server update'] = """
type: command
short-summary: Update a flexible server.
long-summary: |
    > [!WARNING]
    > Enabling High-availability may result in a short downtime for the server based on your server configuration.
examples:
  - name: Update a flexible server's sku, using local context for server and resource group.
    text: az mysql flexible-server update --sku-name Standard_D4ds_v4 --tier GeneralPurpose
  - name: Update a flexible server's tags.
    text: az mysql flexible-server update --resource-group testGroup --name testserver --tags "k1=v1" "k2=v2"
    crafted: true
  - name: Set or change key and identity for data encryption.
    text: >
      # get key identifier of the existing key

      newKeyIdentifier=$(az keyvault key show --vault-name testVault --name testKey \\
        --query key.kid -o tsv)


      # update server with new key/identity

      az mysql flexible-server update --resource-group testGroup --name testserver \\
        --key $newKeyIdentifier --identity newIdentity
  - name: Set or change key, identity, backup key and backup identity for data encryption with geo redundant backup.
    text: >
      # get key identifier of the existing key and backup key

      newKeyIdentifier=$(az keyvault key show --vault-name testVault --name testKey \\
        --query key.kid -o tsv)

      newBackupKeyIdentifier=$(az keyvault key show --vault-name testBackupVault \\
        --name testBackupKey --query key.kid -o tsv)


      # update server with new key/identity and backup key/identity

      az mysql flexible-server update --resource-group testGroup --name testserver \\
        --key $newKeyIdentifier --identity newIdentity \\
        --backup-key $newBackupKeyIdentifier --backup-identity newBackupIdentity
  - name: Disable data encryption for flexible server.
    text: >
      az mysql flexible-server update --resource-group testGroup --name testserver \\
        --disable-data-encryption
"""

helps['mysql flexible-server delete'] = """
type: command
short-summary: Delete a flexible server.
examples:
  - name: Delete a flexible server.
    text: az mysql flexible-server delete --resource-group testGroup --name testserver
  - name: Delete a flexible server without confirmation prompt.
    text: az mysql flexible-server delete --resource-group testGroup --name testserver --yes
"""

helps['mysql flexible-server restore'] = """
type: command
short-summary: Restore a flexible server from backup.
examples:
  - name: >
      Restore 'testserver' to a specific point-in-time as a new server 'testserverNew' with the same network configuration.
    text: az mysql flexible-server restore --resource-group testGroup --name testserverNew --source-server testserver --restore-time "2017-06-15T13:10:00Z"
  - name: >
      Restore public access or private access server 'testserver' as a new server 'testserverNew' with new subnet to current point-in-time.
      New vnet, subnet, and private dns zone for the restored server will be provisioned. Please refer to 'flexible-server create' command for more private access scenarios.
    text: >
      az mysql flexible-server restore --resource-group testGroup --name testserverNew \\
        --source-server testserver --vnet newVnet --subnet newSubnet \\
        --address-prefixes 172.0.0.0/16 --subnet-prefixes 172.0.0.0/24 \\
        --private-dns-zone testDNS.mysql.database.azure.com
  - name: Restore private access server 'testserver' to current point-in-time as a new server 'testserverNew' with public access.
    text: >
      az mysql flexible-server restore --resource-group testGroup --name testserverNew \\
        --source-server testserver --public-access Enabled
  - name: >
      Restore 'testserver' to current point-in-time as a new server 'testserverNew' in a different resource group.
      Here --resource-group is for the target server's resource group, and --source-server must be passed as resource ID.
    text: >
      az mysql flexible-server restore --resource-group testGroup --name testserverNew \\
        --source-server /subscriptions/{sourceSubscriptionId}/resourceGroups/{sourceResourceGroup}/providers/Microsoft.DBforMySQL/flexibleServers/{sourceServerName}
  - name: >
      Restore 'testserver' to current point-in-time as a new server 'testserverNew' in a different subscription.
      Here --resource-group is for the target server's resource group, and --source-server must be passed as resource ID.
      This resource ID can be in a subscription different than the subscription used for az account set.
    text: >
      az mysql flexible-server restore --resource-group testGroup --name testserverNew \\
        --source-server /subscriptions/{sourceSubscriptionId}/resourceGroups/{sourceResourceGroup}/providers/Microsoft.DBforMySQL/flexibleServers/{sourceServerName}
"""

helps['mysql flexible-server geo-restore'] = """
type: command
short-summary: Geo-restore a flexible server from backup.
examples:
  - name: >
      Geo-restore 'testserver' to a new server 'testserverNew' in location 'newLocation' with the same network configuration.
      Private access server will use different private dns zone.
    text: az mysql flexible-server geo-restore --resource-group testGroup --name testserverNew --source-server testserver --location newLocation
  - name: >
      Geo-restore public access or private access server 'testserver' as a new server 'testserverNew' with new subnet.
      New vnet, subnet, and private dns zone for the restored server will be provisioned. Please refer to 'flexible-server create' command for more private access scenarios.
    text: >
      az mysql flexible-server geo-restore --resource-group testGroup --name testserverNew \\
        --source-server testserver --vnet newVnet --subnet newSubnet \\
        --address-prefixes 172.0.0.0/16 --subnet-prefixes 172.0.0.0/24 \\
        --private-dns-zone testDNS.mysql.database.azure.com --location newLocation
  - name: Geo-restore private access server 'testserver' as a new server 'testserverNew' with public access.
    text: >
      az mysql flexible-server geo-restore --resource-group testGroup --name testserverNew  --source-server testserver --public-access Enabled --location newLocation
  - name: >
      Geo-restore 'testserver' to current point-in-time as a new server 'testserverNew' in a different subscription / resource group.
      Here --resource-group is for the target server's resource group, and --source-server must be passed as resource ID.
      This resource ID can be in a subscription different than the subscription used for az account set.
    text: >
      az mysql flexible-server geo-restore --resource-group testGroup --name testserverNew --location newLocation \\
        --source-server /subscriptions/{sourceSubscriptionId}/resourceGroups/{sourceResourceGroup}/providers/Microsoft.DBforMySQL/flexibleServers/{sourceServerName}
"""

helps['mysql flexible-server start'] = """
type: command
short-summary: Start a flexible server.
examples:
  - name: Start a flexible server.
    text: az mysql flexible-server start --resource-group testGroup --name testserver
    crafted: true
"""

helps['mysql flexible-server stop'] = """
type: command
short-summary: Stop a flexible server.
examples:
  - name: Stop a flexible server.
    text: az mysql flexible-server stop --resource-group testGroup --name testserver
    crafted: true
"""

helps['mysql flexible-server restart'] = """
type: command
short-summary: Restart a flexible server.
examples:
  - name: Restart a flexible server.
    text: az mysql flexible-server restart --resource-group testGroup --name testserver
    crafted: true
  - name: Restart a flexible server with failover
    text: az mysql flexible-server restart --resource-group testGroup --name testserver --failover Forced
"""

helps['mysql flexible-server detach-vnet'] = """
type: command
short-summary: Detach vnet for a flexible server.
examples:
  - name: Detach vnet for a flexible server with public access disabled.
    text: az mysql flexible-server detach-vnet --resource-group testGroup --name testserver --public-network-access Disabled
    crafted: true
"""

helps['mysql flexible-server maintenance'] = """
type: group
short-summary: Manage maintenance on a flexible server.
"""

helps['mysql flexible-server maintenance reschedule'] = """
type: command
short-summary: Reschedule the ongoing planned maintenance of a flexible server.
examples:
  - name: reschedule a existing maintenance '_T9Q-TS8' of the server 'testserver' under resource gruop 'testgroup' to a new start time 'UTC 20240601 09:00:00'
    text: az mysql flexible-server maintenance reschedule --resource-group testgroup --server-name testserver --maintenance-name _T9Q-TS8 --start-time 2024-06-01T09:00:00Z
"""

helps['mysql flexible-server maintenance list'] = """
type: command
short-summary: List all of the maintenances of a flexible server.
examples:
  - name: List all of the maintenances of mysql flexible server 'testserver' under resource group 'testgroup'.
    text: az mysql flexible-server maintenance list --resource-group testgroup --server-name testserver
"""

helps['mysql flexible-server maintenance show'] = """
type: command
short-summary: Get the specific maintenance of a flexible server by maintenance name.
examples:
  - name: Get a maintenance of mysql flexible server 'testserver' under resource group 'testgroup', with maintenance name '_T9Q-TS8'
    text: az mysql flexible-server maintenance show --resource-group testgroup --server-name testserver --maintenance-name _T9Q-TS8
"""

helps['mysql flexible-server wait'] = """
type: command
short-summary: Wait for the flexible server to satisfy certain conditions.
examples:
  - name: Wait for the flexible server to satisfy certain conditions.
    text: az mysql flexible-server wait --exists --resource-group testGroup --name testserver
    crafted: true
"""

helps['mysql flexible-server db'] = """
type: group
short-summary: Manage MySQL databases on a flexible server.
"""

helps['mysql flexible-server db create'] = """
type: command
short-summary: Create a MySQL database on a flexible server.
examples:
  - name: >
      Create database 'testDatabase' in the flexible server 'testserver' with default charset utf8 and collation utf8_general_cis.
    text: >
      az mysql flexible-server db create --resource-group testGroup --server-name testserver --database-name testDatabase
  - name: >
      Create database 'testDatabase' in the flexible server 'testserver' with a given character set and collation rules.
    text: >
      az mysql flexible-server db create --resource-group testGroup --server-name testserver --database-name testDatabase --charset validCharset --collation validCollation
"""

helps['mysql flexible-server db delete'] = """
type: command
short-summary: Delete a database on a flexible server.
examples:
  - name: Delete database 'testDatabase' in the flexible server 'testserver'.
    text: az mysql flexible-server db delete --resource-group testGroup --server-name testserver --database-name testDatabase
"""

helps['mysql flexible-server db list'] = """
type: command
short-summary: List the databases for a flexible server.
examples:
  - name: List databases in the flexible server 'testserver'.
    text: az mysql flexible-server db list --resource-group testGroup --server-name testserver
  - name: List databases in the flexible server 'testserver' in table format.
    text: az mysql flexible-server db list --resource-group testGroup --server-name testserver --output table
"""

helps['mysql flexible-server db show'] = """
type: command
short-summary: Show the details of a database.
examples:
  - name: Show database 'testDatabase' in the server 'testserver'.
    text: az mysql flexible-server db show --resource-group testGroup --server-name testserver --database-name testDatabase
"""

helps['mysql flexible-server firewall-rule'] = """
type: group
short-summary: Manage firewall rules for a server.
"""

helps['mysql flexible-server firewall-rule create'] = """
type: command
short-summary: Create a new firewall rule for a flexible server.
examples:
  - name: >
      Create a firewall rule allowing connections from a specific IP address.
    text: >
      az mysql flexible-server firewall-rule create --resource-group testGroup --name testserver --rule-name allowip --start-ip-address 107.46.14.221
  - name: >
      Create a firewall rule allowing connections from an IP address range.
    text: >
        az mysql flexible-server firewall-rule create --resource-group testGroup --name testserver --rule-name allowiprange --start-ip-address 107.46.14.0 --end-ip-address 107.46.14.221
  - name: >
      Create a firewall rule allowing connections to all Azure services
    text: >
      az mysql flexible-server firewall-rule create --resource-group testGroup --name testserver --start-ip-address 0.0.0.0
"""

helps['mysql flexible-server firewall-rule delete'] = """
type: command
short-summary: Delete a firewall rule.
examples:
  - name: Delete a firewall rule.
    text: az mysql flexible-server firewall-rule delete --rule-name testRule --resource-group testGroup --name testserver
  - name: Delete a firewall rule without confirmation.
    text: az mysql flexible-server firewall-rule delete --rule-name testRule --resource-group testGroup --name testserver --yes
"""

helps['mysql flexible-server firewall-rule list'] = """
type: command
short-summary: List all firewall rules for a flexible server.
examples:
  - name: List all firewall rules for a flexible server.
    text: az mysql flexible-server firewall-rule list --resource-group testGroup --name testserver
  - name: List all firewall rules for a flexible server in table format.
    text: az mysql flexible-server firewall-rule list --resource-group testGroup --name testserver --output table
"""

helps['mysql flexible-server firewall-rule show'] = """
type: command
short-summary: Get the details of a firewall rule.
examples:
  - name: Get the details of a firewall rule.
    text: az mysql flexible-server firewall-rule show --rule-name testRule --resource-group testGroup --name testserver
    crafted: true
"""

helps['mysql flexible-server firewall-rule update'] = """
type: command
short-summary: Update a firewall rule.
examples:
  - name: Update a firewall rule's start IP address.
    text: az mysql flexible-server firewall-rule update --resource-group testGroup --name testserver \\
            --rule-name allowiprange --start-ip-address 107.46.14.1
  - name: Update a firewall rule's start and end IP address.
    text: az mysql flexible-server firewall-rule update --resource-group testGroup --name testserver \\
            --rule-name allowiprange --start-ip-address 107.46.14.2 --end-ip-address 107.46.14.218
"""


helps['mysql flexible-server parameter'] = """
type: group
short-summary: Commands for managing server parameter values for flexible server.
"""

helps['mysql flexible-server parameter list'] = """
type: command
short-summary: List the parameter values for a flexible server.
examples:
  - name: List the parameter values for a flexible server.
    text: az mysql flexible-server parameter list --resource-group testGroup --server-name testserver
  - name: List the parameter values for a flexible server in table format.
    text: az mysql flexible-server parameter list --resource-group testGroup --server-name testserver --output table
"""

helps['mysql flexible-server parameter set'] = """
type: command
short-summary: Update the parameter of a flexible server.
examples:
  - name: Set a new parameter value.
    text: az mysql flexible-server parameter set --resource-group testGroup --server-name testserver --name parameterName --value parameterValue
  - name: Set a parameter value to its default.
    text: az mysql flexible-server parameter set --resource-group testGroup --server-name testserver --name parameterName
"""

helps['mysql flexible-server parameter set-batch'] = """
type: command
short-summary: Batch update parameters of a flexible server.
examples:
  - name: Batch set parameters.
    text: az mysql flexible-server parameter set-batch --resource-group testGroup --server-name testserver --source "user-override" --args key1="value1" key2="value2"
"""

helps['mysql flexible-server parameter show'] = """
type: command
short-summary: Get the parameter for a flexible server."
examples:
  - name: Get the parameter for a server.
    text: az mysql flexible-server parameter show --resource-group testGroup --server-name testserver --name parameterName
"""

helps['mysql flexible-server replica'] = """
type: group
short-summary: Manage read replicas.
"""

helps['mysql flexible-server replica create'] = """
type: command
short-summary: Create a read replica for a server.
examples:
  - name: Create a read replica 'testReplicaServer' for 'testserver' in the specified zone if available.
    text: az mysql flexible-server replica create --replica-name testReplicaServer -g testGroup --source-server testserver --zone 3
  - name: >
      Create a read replica 'testReplicaServer' for 'testserver' in a different subscription / resource group 'newTestGroup'.
      Here --resource-group is for the read replica's resource group, and --source-server must be passed as resource ID.
      This resource ID can be in a subscription different than the subscription used for az account set.
    text: >
      az mysql flexible-server replica create --replica-name testReplicaServer -g newTestGroup \\
        --source-server /subscriptions/{sourceSubscriptionId}/resourceGroups/{sourceResourceGroup}/providers/Microsoft.DBforMySQL/flexibleServers/{sourceServerName}
"""

helps['mysql flexible-server replica list'] = """
type: command
short-summary: List all read replicas for a given server.
examples:
  - name: List all read replicas for master server 'testserver'.
    text: az mysql flexible-server replica list -g testGroup -n testserver
"""

helps['mysql flexible-server replica stop-replication'] = """
type: command
short-summary: Stop replication to a read replica and make it a read/write server.
examples:
  - name: Stop replication to 'testReplicaServer' and make it a read/write server.
    text: az mysql flexible-server replica stop-replication -g testGroup -n testReplicaServer
"""

helps['mysql flexible-server list-skus'] = """
type: command
short-summary: Lists available sku's in the given region.
examples:
  - name: Lists available sku's in the given region.
    text: az mysql flexible-server list-skus -l eastus
  - name: Lists available sku's in the given region in table output
    text: az mysql flexible-server list-skus -l eastus -o table
"""

helps['mysql flexible-server show-connection-string'] = """
type: command
short-summary: Show the connection strings for a MySQL flexible-server database.
examples:
  - name: Show connection strings for cmd and programming languages.
    text: az mysql flexible-server show-connection-string -s testserver -u username -p password -d databasename
"""

helps['mysql flexible-server deploy'] = """
type: group
short-summary: Enable and run GitHub Actions workflow for MySQL server
"""

helps['mysql flexible-server deploy setup'] = """
type: command
short-summary: Create GitHub Actions workflow file for MySQL server.
examples:
  - name: Create GitHub Actions workflow file for MySQL server.
    text: az mysql flexible-server deploy setup -s testserver -g testGroup -u username -p password --sql-file test.sql --repo username/userRepo -d flexibleserverdb --action-name testAction
  - name: Create GitHub Actions workflow file for MySQL server and push it to the remote repository
    text: az mysql flexible-server deploy setup -s testserver -g testGroup -u username -p password --sql-file test.sql --repo username/userRepo -d flexibleserverdb --action-name testAction --branch userBranch --allow-push
"""

helps['mysql flexible-server deploy run'] = """
type: command
short-summary: Run an existing workflow in your github repository
examples:
  - name: Run an existing workflow in your github repository
    text: az mysql flexible-server deploy run --action-name testAction --branch userBranch
"""

helps['mysql flexible-server server-logs'] = """
type: group
short-summary: Manage server logs.
"""

helps['mysql flexible-server server-logs download'] = """
type: command
short-summary: Download log files.
examples:
  - name: Download log files f1 and f2 to the current directory from the server 'testsvr'.
    text: az mysql flexible-server server-logs download -g testgroup -s testsvr -n f1.log f2.log
"""

helps['mysql flexible-server server-logs list'] = """
type: command
short-summary: List log files for a server.
examples:
  - name: List log files for 'testsvr' modified in the last 72 hours (default value).
    text: az mysql flexible-server server-logs list -g testgroup -s testsvr
  - name: List log files for 'testsvr' modified in the last 10 hours.
    text: az mysql flexible-server server-logs list -g testgroup -s testsvr --file-last-written 10
  - name: List log files for 'testsvr' less than 30Kb in size.
    text: az mysql flexible-server server-logs list -g testgroup -s testsvr --max-file-size 30
"""

helps['mysql flexible-server upgrade'] = """
type: command
short-summary: Upgrade the major version of a flexible server.
examples:
  - name: Upgrade server 'testsvr' to MySQL major version 8.
    text: >
      # make sure that sql_mode only contains values allowed in new version, for example:

      az mysql flexible-server parameter set -g testgroup -s testsvr -n sql_mode \\
        -v "ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO"

      # upgrade server to MySQL major version 8.

      az mysql flexible-server upgrade -g testgroup -n testsvr -v 8
"""

helps['mysql flexible-server backup'] = """
type: group
short-summary: Manage flexible server backups.
"""

helps['mysql flexible-server backup list'] = """
type: command
short-summary: List all the backups for a given server.
examples:
  - name: List all backups for 'testsvr'.
    text: az mysql flexible-server backup list -g testgroup -n testsvr
"""

helps['mysql flexible-server backup show'] = """
type: command
short-summary: Show the details of a specific backup for a given server.
examples:
  - name: Show the details of backup 'testbackup' for 'testsvr'.
    text: az mysql flexible-server backup show -g testgroup -n testsvr --backup-name testbackup
"""

helps['mysql flexible-server backup create'] = """
type: command
short-summary: Create a backup for a given server with specified backup name.
examples:
  - name: Create a backup for 'testsvr' with backup name 'testbackup'.
    text: az mysql flexible-server backup create -g testgroup -n testsvr --backup-name testbackup
"""

helps['mysql flexible-server backup delete'] = """
type: command
short-summary: Delete a backup for a given server with specified backup name.
examples:
  - name: Delete a backup for 'testsvr' with backup name 'testbackup'.
    text: az mysql flexible-server backup delete -g testgroup -n testsvr --backup-name testbackup
"""

helps['mysql flexible-server identity'] = """
type: group
short-summary: Manage server user assigned identities.
"""

helps['mysql flexible-server identity assign'] = """
type: command
short-summary: Add user asigned managed identities to the server.
examples:
  - name: Add identities 'test-identity' and 'test-identity-2' to server 'testsvr'.
    text: az mysql flexible-server identity assign -g testgroup -s testsvr --identity test-identity test-identity-2
"""

helps['mysql flexible-server identity remove'] = """
type: command
short-summary: Remove user asigned managed identites from the server.
examples:
  - name: Remove identity 'test-identity' from server 'testsvr'.
    text: az mysql flexible-server identity remove -g testgroup -s testsvr --identity test-identity
"""

helps['mysql flexible-server identity show'] = """
type: command
short-summary: Get an user assigned managed identity from the server.
examples:
  - name: Get identity 'test-identity' from server 'testsvr'.
    text: az mysql flexible-server identity show -g testgroup -s testsvr --identity test-identity
"""

helps['mysql flexible-server identity list'] = """
type: command
short-summary: List all user assigned managed identities from the server.
examples:
  - name: List all identities from server 'testsvr'.
    text: az mysql flexible-server identity list -g testgroup -s testsvr
"""

helps['mysql flexible-server ad-admin'] = """
type: group
short-summary: Manage server Active Directory administrator.
"""

helps['mysql flexible-server ad-admin create'] = """
type: command
short-summary: Create an Active Directory administrator.
examples:
  - name: Create Active Directory administrator with user 'john@contoso.com', administrator ID '00000000-0000-0000-0000-000000000000' and identity 'test-identity'.
    text: az mysql flexible-server ad-admin create -g testgroup -s testsvr -u john@contoso.com -i 00000000-0000-0000-0000-000000000000 --identity test-identity
"""

helps['mysql flexible-server ad-admin delete'] = """
type: command
short-summary: Delete an Active Directory administrator.
examples:
  - name: Delete Active Directory administrator.
    text: az mysql flexible-server ad-admin delete -g testgroup -s testsvr
"""

helps['mysql flexible-server ad-admin list'] = """
type: command
short-summary: List all Active Directory administrators.
examples:
  - name: List Active Directory administrators.
    text: az mysql flexible-server ad-admin list -g testgroup -s testsvr
"""

helps['mysql flexible-server ad-admin show'] = """
type: command
short-summary: Get an Active Directory administrator.
examples:
  - name: Get Active Directory administrator.
    text: az mysql flexible-server ad-admin show -g testgroup -s testsvr
"""

helps['mysql flexible-server ad-admin wait'] = """
type: command
short-summary: Wait for the Active Directory administrator to satisfy certain conditions.
examples:
  - name: Wait until the Active Directory administrator exists.
    text: az mysql flexible-server ad-admin wait -g testgroup -s testsvr --exists
  - name: Wait for the Active Directory administrator to be deleted.
    text: az mysql flexible-server ad-admin wait -g testgroup -s testsvr --deleted
"""

helps['mysql flexible-server gtid'] = """
type: group
short-summary: Manage GTID on a server.
"""

helps['mysql flexible-server gtid reset'] = """
type: command
short-summary: Resets GTID on a server.
examples:
  - name: Resets GTID '3E11FA47-71CA-11E1-9E33-C80AA9429562:23' on server 'testsvr'.
    text: az mysql flexible-server gtid reset -g testgroup -s testsvr --gtid-set 3E11FA47-71CA-11E1-9E33-C80AA9429562:23
"""

helps['mysql flexible-server export'] = """
type: group
short-summary: Manage export backup on a server.
"""

helps['mysql flexible-server export create'] = """
type: command
short-summary: Create an export backup for a given server with specified backup name.
examples:
  - name: Create a export backup for 'testsvr' with backup name 'testbackup'.
    text: az mysql flexible-server export create -g testgroup -n testsvr -b testbackup -u destsasuri
"""
