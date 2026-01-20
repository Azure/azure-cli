# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import

# pylint: disable=line-too-long, too-many-lines


helps['postgres'] = """
type: group
short-summary: Manage Azure Database for PostgreSQL.
"""


helps['postgres flexible-server'] = """
type: group
short-summary: Manage Azure Database for PostgreSQL Flexible Servers.
"""

helps['postgres flexible-server create'] = """
type: command
short-summary: Create a PostgreSQL flexible server.
long-summary: >
    Create a PostgreSQL flexible server with custom or default configuration. For more information for network configuration, see

    - Configure public access

    https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-manage-firewall-cli

    - Configure private access

    https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-manage-virtual-network-cli

examples:
  - name: >
      Create a PostgreSQL flexible server with custom parameters
    text: >
        az postgres flexible-server create --location northeurope --resource-group testGroup \\
          --name testserver --admin-user username --admin-password password \\
          --sku-name Standard_D2s_v3 --tier GeneralPurpose --public-access 153.24.26.117 --storage-size 128 \\
          --tags "key=value" --version 18 --zonal-resiliency Enabled --zone 1 \\
          --standby-zone 3
  - name: >
      Create server with high availability feature enabled that allows primary and standby in the same zone when multi-zone capacity is unavailable.
    text: >
      az postgres flexible-server create -g testGroup -n testCluster --location testLocation --zonal-resiliency Enabled --allow-same-zone
  - name: >
      Create a PostgreSQL flexible server using Premium SSD v2 Disks.
    text: >
      # set storage type to "PremiumV2_LRS" and provide values for Storage size (in GiB), IOPS (operations/sec), and Throughput (MB/sec).

      az postgres flexible-server create --location northeurope --resource-group testGroup \\
          --name testserver --admin-user username --admin-password password \\
          --sku-name Standard_B1ms --tier GeneralPurpose --storage-type PremiumV2_LRS --storage-size 128 --iops 3000 --throughput 125
  - name: >
      Create a PostgreSQL flexible server with default parameters and public access enabled by default. \
      Resource group, server name, username, password, and default database will be created by CLI
    text: >
        az postgres flexible-server create
  - name: >
      Create a PostgreSQL flexible server with public access and add the range of IP address to have access to this server.
      The --public-access parameter can be 'Disabled', 'Enabled', 'All', 'None', <startIpAddress>, or <startIpAddress>-<endIpAddress>
    text: >
      az postgres flexible-server create --resource-group testGroup --name testserver --public-access 125.23.54.31-125.23.54.35
  - name: >
      Create a PostgreSQL flexible server with private access. If provided virtual network and subnet do not exists, virtual network and subnet with the specified address prefixes will be created.
    text: >
      az postgres flexible-server create --resource-group testGroup --name testserver --vnet myVnet --subnet mySubnet --address-prefixes 10.0.0.0/16 --subnet-prefixes 10.0.0.0/24
  - name: >
      Create a PostgreSQL flexible server using a new subnet resource ID and new private DNS zone resource ID. The subnet and DNS zone can be created in different subscription or resource group.
    text: |
      az postgres flexible-server create \\
        --resource-group testGroup --name testserver \\
        --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNetName}/subnets/{SubnetName} \\
        --private-dns-zone /subscriptions/{SubID}/resourceGroups/{resourceGroup}/providers/Microsoft.Network/privateDnsZones/testPostgreSQLFlexibleDnsZone.private.postgres.database.azure.com \\
        --address-prefixes 172.0.0.0/16 --subnet-prefixes 172.0.0.0/24
  - name: >
      Create a PostgreSQL flexible server using existing network resources in the same resource group.
      The provided subnet should not have any other resource deployed in it and this subnet will be delegated to Microsoft.DBforPostgreSQL/flexibleServers, if not already delegated.
      The private DNS zone will be linked to the virtual network if not already linked.
    text: >
      # create vnet

      az network vnet create --resource-group testGroup --name testVnet --location testLocation --address-prefixes 172.0.0.0/16


      # create subnet

      az network vnet subnet create --resource-group testGroup --vnet-name testVnet --address-prefixes 172.0.0.0/24 --name testSubnet


      # create private dns zone

      az network private-dns zone create -g testGroup -n testDNS.private.postgres.database.azure.com


      az postgres flexible-server create --resource-group testGroup \\
        --name testserver --location testLocation \\
        --subnet /subscriptions/{SubId}/resourceGroups/{testGroup}/providers/Microsoft.Network/virtualNetworks/tesetVnet/subnets/testSubnet \\
        --private-dns-zone /subscriptions/{SubId}/resourceGroups/{testGroup}/providers/Microsoft.Network/privateDnsZones/testDNS.postgres.database.azure.com\\


      az postgres flexible-server create --resource-group testGroup --name testserver \\
        --vnet testVnet --subnet testSubnet --location testLocation \\
        --private-dns-zone /subscriptions/{SubId}/resourceGroups/{testGroup}/providers/Microsoft.Network/privateDnsZones/testDNS.postgres.database.azure.com
  - name: >
      Create a PostgreSQL flexible server using existing network resources in the different resource group / subscription.
    text: >
      az postgres flexible-server create --resource-group testGroup \\
         --name testserver --location testLocation \\
        --subnet /subscriptions/{SubId2}/resourceGroups/{testGroup2}/providers/Microsoft.Network/virtualNetworks/tesetVnet/subnets/testSubnet \\
        --private-dns-zone /subscriptions/{SubId2}/resourceGroups/{testGroup2}/providers/Microsoft.Network/privateDnsZones/testDNS.postgres.database.azure.com
  - name: >
      Create a PostgreSQL flexible server with data encryption.
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

      az postgres flexible-server create -g testGroup -n testServer --location testLocation \\
        --key $keyIdentifier --identity testIdentity
  - name: >
      Create a PostgreSQL flexible server with Microsoft Entra auth as well as password auth.
    text: >
      # create flexible server with aad auth and password auth enabled

      az postgres flexible-server create -g testGroup -n testServer --location testLocation \\
        --microsoft-entra-auth Enabled
  - name: >
      Create a PostgreSQL flexible server with Microsoft Entra auth only and primary administrator specified.
    text: >
      # create flexible server with aad only auth and password auth disabled with primary administrator specified

      az postgres flexible-server create -g testGroup -n testServer --location testLocation \\
        --microsoft-entra-auth Enabled --password-auth Disabled \\
        --admin-object-id 00000000-0000-0000-0000-000000000000 --admin-display-name john@contoso.com --admin-type User
  - name: >
      Create a PostgreSQL flexible server with public access, geo-redundant backup enabled and add the range of IP address to have access to this server.
      The --public-access parameter can be 'All', 'None', <startIpAddress>, or <startIpAddress>-<endIpAddress>
    text: >
      az postgres flexible-server create --resource-group testGroup --name testserver --geo-redundant-backup Enabled --public-access 125.23.54.31-125.23.54.35
  - name: >
      Create a PostgreSQL flexible server with data encryption for geo-rundundant backup enabled server.
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

      # create keyvault in geo-paired region

      az keyvault create -g testGroup -n geoVault --location geoPairedLocation \\
        --enable-purge-protection true


      # create key in keyvault and save its key identifier

      geoKeyIdentifier=$(az keyvault key create --name geoKey -p software \\
        --vault-name geoVault --query key.kid -o tsv)


      # create identity in geo-raired location and save its principalId

      geoIdentityPrincipalId=$(az identity create -g testGroup --name geoIdentity \\
        --location geoPairedLocation --query principalId -o tsv)


      # add testIdentity as an access policy with key permissions 'Wrap Key', 'Unwrap Key', 'Get' and 'List' inside testVault

      az keyvault set-policy -g testGroup -n geoVault --object-id $geoIdentityPrincipalId \\
        --key-permissions wrapKey unwrapKey get list


      # create flexible server with data encryption enabled for geo-backup Enabled server

      az postgres flexible-server create -g testGroup -n testServer --location testLocation --geo-redundant-backup Enabled \\
        --key $keyIdentifier --identity testIdentity --backup-key $geoKeyIdentifier --backup-identity geoIdentity

  - name: >
      Create flexible server with custom storage performance tier. Accepted values "P4", "P6", "P10", "P15", "P20", "P30", \\
      "P40", "P50", "P60", "P70", "P80". Actual allowed values depend on the --storage-size selection for flexible server creation. \\
      Default value for storage performance tier depends on the --storage-size selected for flexible server creation.
    text: >
      az postgres flexible-server create -g testGroup -n testServer --location testLocation --performance-tier P15

  - name: >
      Create flexible server with storage auto-grow as Enabled. Accepted values Enabled / Disabled. Default value for storage auto-grow is "Disabled".
    text: >
      az postgres flexible-server create -g testGroup -n testServer --location testLocation --storage-auto-grow Enabled

  - name: >
      Create elastic cluster with node count of 5. Default node count is 2 when --cluster-option is "ElasticCluster".
    text: >
      az postgres flexible-server create -g testGroup -n testCluster --location testLocation --cluster-option ElasticCluster --node-count 5
"""

helps['postgres flexible-server show'] = """
type: command
short-summary: Get the details of a flexible server.
examples:
  - name: Get the details of a flexible server
    text: az postgres flexible-server show --resource-group testGroup --name testserver
"""

helps['postgres flexible-server list'] = """
type: command
short-summary: List available flexible servers.
examples:
  - name: List all PostgreSQL flexible servers in a subscription.
    text: az postgres flexible-server list
  - name: List all PostgreSQL flexible servers in a resource group.
    text: az postgres flexible-server list --resource-group testGroup
  - name: List all PostgreSQL flexible servers in a resource group in table format.
    text: az postgres flexible-server list --resource-group testGroup --output table
"""

helps['postgres flexible-server update'] = """
type: command
short-summary: Update a flexible server.
examples:
  - name: Update a flexible server's sku, using local context for server and resource group.
    text: az postgres flexible-server update --sku-name Standard_D4s_v3
  - name: Update a server's tags.
    text: az postgres flexible-server update --resource-group testGroup --name testserver --tags "k1=v1" "k2=v2"
  - name: Reset password
    text: az postgres flexible-server update --resource-group testGroup --name testserver -p password123
  - name: Update a flexible server to enable Microsoft Entra auth for password auth enabled server
    text: az postgres flexible-server update --resource-group testGroup --name testserver --microsoft-entra-auth Enabled
  - name: Change key/identity for data encryption. Data encryption cannot be enabled post server creation, this will only update the key/identity.
    text: >
      # get key identifier of the existing key

      newKeyIdentifier=$(az keyvault key show --vault-name testVault --name testKey \\
        --query key.kid -o tsv)


      # update server with new key/identity

      az postgres flexible-server update --resource-group testGroup --name testserver \\
        --key $newKeyIdentifier --identity newIdentity
  - name: Update a flexible server to update private DNS zone for a VNET enabled server, using private DNS zone in the same resource group and subscription. Private DNS zone will be created Private DNS zone will be linked to the VNET if not already linked.
    text: az postgres flexible-server update --resource-group testGroup --name testserver --private-dns-zone testDNS2.postgres.database.azure.com
  - name: Update a flexible server to update private DNS zone for a VNET enabled server, using private DNS zone in the different resource group and subscription. Private DNS zone will be linked to the VNET if not already linked.
    text: az postgres flexible-server update --resource-group testGroup --name testserver --private-dns-zone /subscriptions/{SubId2}/resourceGroups/{testGroup2}/providers/Microsoft.Network/privateDnsZones/testDNS.postgres.database.azure.com
  - name: Update a flexible server's storage to enable / disable storage auto-grow.
    text: az postgres flexible-server update --resource-group testGroup --name testserver --storage-auto-grow Enabled
  - name: Update a flexible server's storage to set custom storage performance tier.
    text: az postgres flexible-server update --resource-group testGroup --name testserver --performance-tier P15
  - name: Update a flexible server's storage to set IOPS (operations/sec). Server must be using Premium SSD v2 Disks.
    text: az postgres flexible-server update --resource-group testGroup --name testserver --iops 3000
  - name: Update a flexible server's storage to set Throughput (MB/sec). Server must be using Premium SSD v2 Disks.
    text: az postgres flexible-server update --resource-group testGroup --name testserver --throughput 125
  - name: Update a flexible server's cluster size by scaling up node count. Must be an Elastic Cluster.
    text: az postgres flexible-server update --resource-group testGroup --name testcluster --node-count 6
"""

helps['postgres flexible-server restore'] = """
type: command
short-summary: Restore a flexible server from backup.
examples:
  - name: Restore 'testserver' to a specific point-in-time as a new server 'testserverNew'.
    text: az postgres flexible-server restore --resource-group testGroup --name testserverNew --source-server testserver --restore-time "2017-06-15T13:10:00Z"
  - name: Restore 'testserver' to current point-in-time as a new server 'testserverNew'.
    text: az postgres flexible-server restore --resource-group testGroup --name testserverNew --source-server testserver
  - name: >
      Restore 'testserver' to current point-in-time as a new server 'testserverNew' in a different resource group. \\
      Here --resource-group is for the target server's resource group, and --source-server must be passed as resource ID.
    text: >
      az postgres flexible-server restore --resource-group testGroup --name testserverNew \\
        --source-server /subscriptions/{testSubscription}/resourceGroups/{sourceResourceGroup}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{sourceServerName}
  - name: >
      Restore 'testserver' to current point-in-time as a new server 'testserverNew' in a different subscription. \\
      Here --resource-group is for the target server's resource group, and --source-server must be passed as resource ID. \\
      This resource ID can be in a subscription different than the subscription used for az account set.
    text: >
      az postgres flexible-server restore --resource-group testGroup --name testserverNew \\
        --source-server /subscriptions/{sourceSubscriptionId}/resourceGroups/{sourceResourceGroup}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{sourceServerName}
  - name: Restore 'testserver' to current point-in-time as a new server 'testserverNew' using Premium SSD v2 Disks by setting storage type to "PremiumV2_LRS"
    text: az postgres flexible-server restore --resource-group testGroup --name testserverNew --source-server testserver --storage-type PremiumV2_LRS
"""

helps['postgres flexible-server restart'] = """
type: command
short-summary: Restart a flexible server.
examples:
  - name: Restart a flexible server.
    text: az postgres flexible-server restart --resource-group testGroup --name testserver
  - name: Restart a server with planned failover
    text: az postgres flexible-server restart --resource-group testGroup --name testserver --failover Planned
  - name: Restart a server with forced failover
    text: az postgres flexible-server restart --resource-group testGroup --name testserver --failover Forced
"""

helps['postgres flexible-server start'] = """
type: command
short-summary: Start a flexible server.
examples:
  - name: Start a flexible server.
    text: az postgres flexible-server start --resource-group testGroup --name testserver
"""

helps['postgres flexible-server stop'] = """
type: command
short-summary: Stop a flexible server.
examples:
  - name: Stop a flexible server.
    text: az postgres flexible-server stop --resource-group testGroup --name testserver
"""

helps['postgres flexible-server wait'] = """
type: command
short-summary: Wait for the flexible server to satisfy certain conditions.
example:
  - name: Wait for the flexible server to satisfy certain conditions.
    text: az postgres flexible-server wait --exists --resource-group testGroup --name testserver
"""

helps['postgres flexible-server delete'] = """
type: command
short-summary: Delete a flexible server.
examples:
  - name: Delete a flexible server.
    text: az postgres flexible-server delete --resource-group testGroup --name testserver
  - name: Delete a flexible server without prompt or confirmation.
    text: az postgres flexible-server delete --resource-group testGroup --name testserver --yes
"""

helps['postgres flexible-server db'] = """
type: group
short-summary: Manage PostgreSQL databases on a flexible server.
"""

helps['postgres flexible-server db create'] = """
type: command
short-summary: Create a PostgreSQL database on a flexible server.
examples:
  - name: Create database 'testDatabase' in the flexible server 'testserver' with the default parameters.
    text: az postgres flexible-server db create --resource-group testGroup --server-name testserver --database-name testDatabase
  - name: Create database 'testDatabase' in the flexible server 'testserver' with a given character set and collation rules.
    text: az postgres flexible-server db create --resource-group testGroup --server-name testserver --database-name testDatabase \\
            --charset validCharset --collation validCollation
"""

helps['postgres flexible-server db delete'] = """
type: command
short-summary: Delete a database on a flexible server.
examples:
  - name: Delete database 'testDatabase' in the flexible server 'testserver'.
    text: az postgres flexible-server db delete --resource-group testGroup --server-name testserver --database-name testDatabase
"""

helps['postgres flexible-server db list'] = """
type: command
short-summary: List the databases for a flexible server.
examples:
  - name: List databases in the flexible server 'testserver'.
    text: az postgres flexible-server db list --resource-group testGroup --server-name testserver
  - name: List databases in the flexible server 'testserver' in table format.
    text: az postgres flexible-server db list --resource-group testGroup --server-name testserver --output table
"""

helps['postgres flexible-server db show'] = """
type: command
short-summary: Show the details of a database.
examples:
  - name: Show database 'testDatabase' in the server 'testserver'.
    text: az postgres flexible-server db show --resource-group testGroup --server-name testserver --database-name testDatabase
"""

helps['postgres flexible-server firewall-rule'] = """
type: group
short-summary: Manage firewall rules for a server.
"""

helps['postgres flexible-server firewall-rule create'] = """
type: command
short-summary: Create a new firewall rule for a flexible server.
examples:
  - name: >
      Create a firewall rule allowing connections from a specific IP address.
    text: >
      az postgres flexible-server firewall-rule create --resource-group testGroup --name testserver --rule-name allowip --start-ip-address 107.46.14.221
  - name: >
      Create a firewall rule allowing connections from an IP address range.
    text: >
        az postgres flexible-server firewall-rule create --resource-group testGroup --name testserver --rule-name allowiprange --start-ip-address 107.46.14.0 --end-ip-address 107.46.14.221
  - name: >
      Create a firewall rule allowing connections to all Azure services
    text: >
      az postgres flexible-server firewall-rule create --resource-group testGroup --name testserver --rule-name allowazureservices --start-ip-address 0.0.0.0
"""

helps['postgres flexible-server firewall-rule list'] = """
type: command
short-summary: List all firewall rules for a flexible server.
example:
  - name: List all firewall rules for a server.
    text: az postgres flexible-server firewall-rule list --resource-group testGroup --name testserver
  - name: List all firewall rules for a server in table format.
    text: az postgres flexible-server firewall-rule list --resource-group testGroup --name testserver --output table
"""

helps['postgres flexible-server firewall-rule show'] = """
type: command
short-summary: Get the details of a firewall rule.
examples:
  - name: Get the details of a firewall rule.
    text: az postgres flexible-server firewall-rule show --rule-name testRule --resource-group testGroup --name testserver
"""

helps['postgres flexible-server firewall-rule update'] = """
type: command
short-summary: Update a firewall rule.
examples:
  - name: Update a firewall rule's start IP address.
    text: az postgres flexible-server firewall-rule update --resource-group testGroup --name testserver --rule-name allowiprange --start-ip-address 107.46.14.1
  - name: Update a firewall rule's start and end IP address.
    text: az postgres flexible-server firewall-rule update --resource-group testGroup --name testserver --rule-name allowiprange --start-ip-address 107.46.14.2 --end-ip-address 107.46.14.218
"""

helps['postgres flexible-server firewall-rule delete'] = """
type: command
short-summary: Delete a firewall rule.
examples:
  - name: Delete a firewall rule.
    text: az postgres flexible-server firewall-rule delete --rule-name testRule --resource-group testGroup --name testserver
"""

helps['postgres flexible-server virtual-endpoint'] = """
type: group
short-summary: Manage virtual endpoints for a PostgreSQL flexible server.
"""

helps['postgres flexible-server virtual-endpoint create'] = """
type: command
short-summary: Create a new virtual endpoint for a flexible server.
examples:
  - name: >
      Create a virtual endpoint with writer endpoint.
    text: >
      az postgres flexible-server virtual-endpoint create --resource-group testGroup --server-name testserver --name test-virtual-endpoint --endpoint-type ReadWrite --members testReplica1
"""

helps['postgres flexible-server virtual-endpoint list'] = """
type: command
short-summary: List all virtual endpoints for a flexible server.
example:
  - name: List all virtual endpoints for a flexible server.
    text: az postgres flexible-server virtual-endpoint list --resource-group testGroup --server-name testserver
"""

helps['postgres flexible-server virtual-endpoint show'] = """
type: command
short-summary: Get the details of a virtual endpoint.
examples:
  - name: Get the details of a virtual endpoint.
    text: az postgres flexible-server virtual-endpoint show --resource-group testGroup --server-name testserver --name test-virtual-endpoint
"""

helps['postgres flexible-server virtual-endpoint update'] = """
type: command
short-summary: Update a virtual endpoint.
examples:
  - name: Update a virtual endpoint.
    text: az postgres flexible-server virtual-endpoint update --resource-group testGroup --server-name testserver --name test-virtual-endpoint --endpoint-type ReadWrite --members testReplica1
"""

helps['postgres flexible-server virtual-endpoint delete'] = """
type: command
short-summary: Delete a virtual endpoint.
examples:
  - name: Delete a virtual endpoint.
    text: az postgres flexible-server virtual-endpoint delete --resource-group testGroup --server-name testserver --name test-virtual-endpoint
"""

helps['postgres flexible-server migration'] = """
type: group
short-summary: Manage migration workflows for PostgreSQL Flexible Servers.
"""

helps['postgres flexible-server migration create'] = """
type: command
short-summary: Create a new migration workflow for a flexible server.
examples:
  - name: >
      Start a migration workflow on the target server identified by the parameters. The configurations of the migration should be specified in the properties file. The different properties are defined as: \n
      sourceDbServerResourceId: Source server details. \n
      adminCredentials: This parameter lists passwords for admin users for both the source server and the target PostgreSQL flexible server. \n
      targetServerUserName: The default value is the admin user created during the creation of the PostgreSQL target flexible server, and the password provided is used for authentication against this user. \n
      dbsToMigrate: Specify the list of databases that you want to migrate to Flexible Server. \n
      overwriteDBsInTarget: When set to true (default), if the target server happens to have an existing database with the same name as the one you're trying to migrate, the migration service automatically overwrites the database. \n
      Sample migrationConfig.json for PostgreSQLSingleServer shown below. \n
      {
        "properties": {
          "sourceDBServerResourceId": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/test-single-rg/providers/Microsoft.DBforPostgreSQL/servers/pg-single-1",
          "secretParameters": {
            "adminCredentials": {
              "sourceServerPassword": "password",
              "targetServerPassword": "password"
            },
            "sourceServerUserName": "testuser@pg-single-1",
            "targetServerUserName": "fspguser"
          },
          "dBsToMigrate": [
            "postgres"
          ],
          "overwriteDbsInTarget": "true"
        }
      }
    text: >
      az postgres flexible-server migration create --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver \
      --migration-name testmigration --properties "migrationConfig.json"
  - name: >
      Start a migration workflow on the target server identified by the parameters. The configurations of the migration should be specified in the migrationConfig.json file. \
      Use --migration-mode offline for Offline migration.
    text: >
      az postgres flexible-server migration create --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver \
      --migration-name testmigration --properties "migrationConfig.json" --migration-mode offline
  - name: >
      Start a migration workflow on the target server identified by the parameters. The configurations of the migration should be specified in the migrationConfig.json file. \
      Use --migration-mode online for Online(with CDC) migration. Use migration-option Validate for validate only request.
    text: >
      az postgres flexible-server migration create --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver \
      --migration-name testmigration --properties "migrationConfig.json" --migration-mode online --migration-option Validate
  - name: >
      Start a migration workflow on the target server identified by the parameters. The configurations of the migration should be specified in the migrationConfig.json file. \
      Use --migration-option Migrate for Migrate Only request.
    text: >
      az postgres flexible-server migration create --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver \
      --migration-name testmigration --properties "migrationConfig.json" --migration-option Migrate
  - name: >
      To start a migration for other than PostgreSQLSingleServer, soureType and sslMode must be specified in properties file. These properties are defined as: \n
      sourceType: Values can be - OnPremises, AWS_AURORA, AWS_RDS, AzureVM, PostgreSQLSingleServer \n
      sslMode:  SSL modes for migration. SSL mode for PostgreSQLSingleServer is VerifyFull and Prefer/Require for other source types. \n
      Sample migrationConfig.json shown below. \n
      {
        "properties": {
          "sourceDBServerResourceId": "<<hostname or IP address>>:<<port>>@<<username>>",
          "secretParameters": {
            "adminCredentials": {
              "sourceServerPassword": "password",
              "targetServerPassword": "password"
            },
            "sourceServerUserName": "postgres",
            "targetServerUserName": "fspguser"
          },
          "dBsToMigrate": [
            "ticketdb","timedb","inventorydb"
          ],
          "overwriteDbsInTarget": "true",
          "sourceType": "OnPremises",
          "sslMode": "Prefer"
        }
      }
    text: >
      az postgres flexible-server migration create --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver \
        --migration-name testmigration --properties "migrationConfig.json"
  - name: >
      Start a private endpoint enabled migration workflow on the target server by specifying migrationRuntimeResourceId in properties file. This property is defined as: \n
      migrationRuntimeResourceId: The resource ID of the migration runtime server that is responsible for migrating data between source and target server. \n
      Sample migrationConfig.json shown below. \n
      {
        "properties": {
          "sourceDBServerResourceId": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/test-single-rg/providers/Microsoft.DBforPostgreSQL/servers/pg-single-1",
          "migrationRuntimeResourceId": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/testGroup/providers/Microsoft.DBforPostgreSQL/flexibleServers/testsourcemigration",
          "secretParameters": {
            "adminCredentials": {
              "sourceServerPassword": "password",
              "targetServerPassword": "password"
            },
            "sourceServerUserName": "testuser@pg-single-1",
            "targetServerUserName": "fspguser"
          },
          "dBsToMigrate": [
            "postgres"
          ],
          "overwriteDbsInTarget": "true"
        }
      }
    text: >
      az postgres flexible-server migration create --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name testmigration
      --properties "migrationConfig.json"
"""

helps['postgres flexible-server migration list'] = """
type: command
short-summary: List the migrations of a flexible server.
examples:
  - name: List the currently active migrations of a target flexible server.
    text: az postgres flexible-server migration list --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --filter Active
  - name: List all (Active/Completed) migrations of a target flexible server.
    text: az postgres flexible-server migration list --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --filter All
"""

helps['postgres flexible-server migration show'] = """
type: command
short-summary: Get the details of a specific migration.
examples:
  - name: Get the details of a specific migration of a target flexible server.
    text: az postgres flexible-server migration show --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name testmigration
"""

helps['postgres flexible-server migration update'] = """
type: command
short-summary: Update a specific migration.
examples:
  - name: Allow the migration workflow to setup logical replication on the source. Note that this command will restart the source server.
    text: az postgres flexible-server migration update --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name testmigration --setup-replication
  - name: Cut-over the data migration for all the databases involved in the migration. After this is complete, subsequent updates to all databases in the migration will not be migrated to the target. Cutover migration can only be triggered for migration_mode=Online.
    text: az postgres flexible-server migration update --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name testmigration --cutover
  - name: Cancels the data migration for all the databases involved in the migration. Only 'InProgress' migration can be cancelled
    text: az postgres flexible-server migration update --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name testmigration --cancel
"""

helps['postgres flexible-server migration check-name-availability'] = """
type: command
short-summary: Checks if the provided migration-name can be used.
examples:
  - name: Check if the migration-name provided is available for your migration workflow.
    text: az postgres flexible-server migration check-name-availability --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
"""

helps['postgres flexible-server parameter'] = """
type: group
short-summary: Commands for managing server parameter values for flexible server.
"""

helps['postgres flexible-server parameter list'] = """
type: command
short-summary: List the parameter values for a flexible server.
examples:
  - name: List the parameter values for a flexible server.
    text: az postgres flexible-server parameter list --resource-group testGroup --server-name servername
  - name: List the parameter values for a flexible server in table format.
    text: az postgres flexible-server parameter list --resource-group testGroup --server-name servername --output table
"""

helps['postgres flexible-server parameter set'] = """
type: command
short-summary: Update the parameter of a flexible server.
examples:
  - name: Set a new parameter value.
    text: az postgres flexible-server parameter set --resource-group testGroup --server-name servername --name parameterName --value parameterValue
  - name: Set a parameter value to its default.
    text: az postgres flexible-server parameter set --resource-group testGroup --server-name servername --name parameterName
"""

helps['postgres flexible-server parameter show'] = """
type: command
short-summary: Get the parameter for a flexible server."
examples:
  - name: Get the parameter for a server.
    text: az postgres flexible-server parameter show --resource-group testGroup --server-name servername --name parameterName
"""

helps['postgres flexible-server list-skus'] = """
type: command
short-summary: Lists available sku's in the given region.
example:
  - name: Lists available sku's in the given region.
    text: az postgres flexible-server list-skus -l eastus --output table
"""

helps['postgres flexible-server show-connection-string'] = """
type: command
short-summary: Show the connection strings for a PostgreSQL flexible-server database.
examples:
  - name: Show connection strings for cmd and programming languages.
    text: az postgres flexible-server show-connection-string -s testserver -u username -p password -d databasename
  - name: Show connection strings for cmd and programming languages with PgBouncer enabled.
    text: az postgres flexible-server show-connection-string -s testserver -u username -p password -d databasename --pg-bouncer
"""

helps['postgres flexible-server deploy'] = """
type: group
short-summary: Enable and run GitHub Actions workflow for PostgreSQL server
"""

helps['postgres flexible-server deploy setup'] = """
type: command
short-summary: Create GitHub Actions workflow file for PostgreSQL server.
examples:
  - name: Create GitHub Actions workflow file for PostgreSQL server.
    text: az postgres flexible-server deploy setup -s testserver -g testGroup -u username -p password --sql-file test.sql --repo username/userRepo -d flexibleserverdb --action-name testAction
  - name: Create GitHub Actions workflow file for PostgreSQL server and push it to the remote repository
    text: az postgres flexible-server deploy setup -s testserver -g testGroup -u username -p password --sql-file test.sql --repo username/userRepo -d flexibleserverdb --action-name testAction --branch userBranch --allow-push
"""

helps['postgres flexible-server deploy run'] = """
type: command
short-summary: Run an existing workflow in your github repository
examples:
  - name: Run an existing workflow in your github repository
    text: az postgres flexible-server deploy run --action-name testAction --branch userBranch
"""

helps['postgres flexible-server backup'] = """
type: group
short-summary: Manage flexible server backups.
"""

helps['postgres flexible-server backup create'] = """
type: command
short-summary: Create a new backup for a flexible server.
examples:
  - name: >
      Create a backup.
    text: >
      az postgres flexible-server backup create -g testgroup -n testsvr --backup-name testbackup
"""

helps['postgres flexible-server backup list'] = """
type: command
short-summary: List all the backups for a given server.
examples:
  - name: List all backups for 'testsvr'.
    text: az postgres flexible-server backup list -g testgroup -n testsvr
"""

helps['postgres flexible-server backup show'] = """
type: command
short-summary: Show the details of a specific backup for a given server.
examples:
  - name: Show the details of backup 'testbackup' for 'testsvr'.
    text: az postgres flexible-server backup show -g testgroup -n testsvr --backup-name testbackup
"""

helps['postgres flexible-server backup delete'] = """
type: command
short-summary: Delete a specific backup.
examples:
  - name: Delete a backup.
    text: az postgres flexible-server backup delete -g testgroup -n testsvr --backup-name testbackup
"""

helps['postgres flexible-server long-term-retention'] = """
type: group
short-summary: Manage flexible server long-term-retention backups.
"""

helps['postgres flexible-server long-term-retention pre-check'] = """
type: command
short-summary: Performs all the checks that are needed for the subsequent long-term-retention backup operation to succeed.
examples:
  - name: Precheck if we can perform long-term-retention command on server 'server-name' on resource group 'resource-group-name' with backup name 'backup-name'.
    text: az postgres flexible-server long-term-retention pre-check -g resource-group-name -b backup-name -n server-name
"""

helps['postgres flexible-server long-term-retention start'] = """
type: command
short-summary: Start long-term-retention backup for a flexible server. SAS URL parameter refers to the container SAS URL, inside the storage account, where the backups will be uploaded.
examples:
  - name: Create a backup with name 'backup-name' of server 'server-name' in resource group 'resource-group-name', using container with SAS URL '<sas-url>'.
    text: az postgres flexible-server long-term-retention start -g resource-group-name -b backup-name -n server-name -u <sas-url>
"""

helps['postgres flexible-server long-term-retention show'] = """
type: command
short-summary: Show the details of a specific long-term-retention backup for a given server.
examples:
  - name: Show the details of long-term-retention backup 'testbackup' for 'testsvr'.
    text: az postgres flexible-server long-term-retention show -g resource-group-name -n server-name -b backup-name
"""

helps['postgres flexible-server long-term-retention list'] = """
type: command
short-summary: List all the long-term-retention backups for a given server.
examples:
  - name: List all long-term-retention backups for 'testsvr'.
    text: az postgres flexible-server long-term-retention list -g resource-group-name -n server-name
"""

helps['postgres flexible-server replica'] = """
type: group
short-summary: Manage read replicas.
"""

helps['postgres flexible-server replica create'] = """
type: command
short-summary: Create a read replica for a server.
examples:
  - name: Create a read replica 'testreplicaserver' for 'testserver' with public or private access in the specified zone and location if available.
    text: az postgres flexible-server replica create --name testreplicaserver -g testGroup --source-server testserver --zone 3 --location testLocation
  - name: Create a read replica 'testreplicaserver' with new subnet for 'testserver' with private access.
    text: >
      az postgres flexible-server replica create --name testreplicaserver -g testGroup \\
        --source-server testserver --zone 3 --location testLocation \\
        --vnet newVnet --subnet newSubnet \\
        --address-prefixes 172.0.0.0/16 --subnet-prefixes 172.0.0.0/24 \\
        --private-dns-zone testDNS.postgres.database.azure.com \\
        --tags "key=value"
  - name: >
      Create a read replica 'testreplicaserver' for 'testserver' with public or private access \
      in the specified location if available. Since zone is not passed, it will automatically pick up zone in the \
      replica location which is different from source server, if available, else will pick up zone same as source server \
      in the replica location if available, else will set the zone as None, i.e. No preference
    text: az postgres flexible-server replica create --name testreplicaserver -g testGroup --source-server testserver --location testLocation
  - name: Create a read replica 'testreplicaserver' for 'testserver' with custom --storage-size and --sku.
    text: az postgres flexible-server replica create --name testreplicaserver -g testGroup --source-server testserver --sku-name Standard_D4ds_v5 --storage-size 256
  - name: Create a read replica 'testreplicaserver' for 'testserver', where 'testreplicaserver' is in a different resource group 'newTestGroup'. \
      Here --resource-group is for the read replica's resource group, and --source-server must be passed as resource ID.
    text: >
      az postgres flexible-server replica create --name testreplicaserver -g newTestGroup \
        --source-server /subscriptions/{sourceSubscriptionId}/resourceGroups/{sourceResourceGroup}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{sourceServerName} --location testLocation
"""

helps['postgres flexible-server replica list'] = """
type: command
short-summary: List all read replicas for a given server.
examples:
  - name: List all read replicas for master server 'testserver'.
    text: az postgres flexible-server replica list -g testGroup -n testserver
"""

helps['postgres flexible-server replica promote'] = """
type: command
short-summary: Stop replication of a read replica and promote it to an independent server or as a primary server.
examples:
  - name: Stop replication to 'testreplicaserver' and promote it a standalone read/write server.
    text: az postgres flexible-server replica promote -g testGroup -n testreplicaserver
  - name: Stop replication to 'testreplicaserver' and promote it a standalone read/write server with forced data sync.
    text: az postgres flexible-server replica promote -g testGroup -n testreplicaserver --promote-mode standalone --promote-option forced
  - name: >
      Stop replication to 'testreplicaserver' and promote it to primary server with planned data sync. \
      The replica you are promoting must have the reader virtual endpoint assigned, or you will receive an error on promotion.
    text: az postgres flexible-server replica promote -g testGroup -n testreplicaserver --promote-mode switchover --promote-option planned
"""

helps['postgres flexible-server geo-restore'] = """
type: command
short-summary: Geo-restore a flexible server from backup.
examples:
  - name: >
      Geo-restore public access server 'testserver' to a new server 'testserverNew' in location 'newLocation' with public access.
    text: az postgres flexible-server geo-restore --resource-group testGroup --name testserverNew --source-server testserver --location newLocation
  - name: >
      Geo-restore private access server 'testserver' as a new server 'testserverNew' with new subnet.
      New vnet, subnet, and private dns zone for the restored server will be provisioned. Please refer to 'flexible-server create' command for more private access scenarios.
    text: >
      az postgres flexible-server geo-restore --resource-group testGroup --name testserverNew \\
        --source-server testserver --vnet newVnet --subnet newSubnet \\
        --address-prefixes 172.0.0.0/16 --subnet-prefixes 172.0.0.0/24 \\
        --private-dns-zone testDNS.postgres.database.azure.com --location newLocation
  - name: >
      Geo-restore 'testserver' to current point-in-time as a new server 'testserverNew' in a different subscription / resource group. \\
      Here --resource-group is for the target server's resource group, and --source-server must be passed as resource ID. \\
      This resource ID can be in a subscription different than the subscription used for az account set.
    text: >
      az postgres flexible-server geo-restore --resource-group testGroup --name testserverNew --location newLocation \\
        --source-server /subscriptions/{sourceSubscriptionId}/resourceGroups/{sourceResourceGroup}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{sourceServerName}
"""

helps['postgres flexible-server revive-dropped'] = """
type: command
short-summary: Revive a dropped flexible server from backup.
examples:
  - name: >
      Revive dropped public access server 'testserver' to a new server 'testserverNew' in location 'newLocation' with public access.
    text: az postgres flexible-server revive-dropped --resource-group testGroup --name testserverNew --source-server /subscriptions/{SubId}/resourceGroups/{testGroup}/providers/Microsoft.DBforPostgreSQL/flexibleServers/testserver --location newLocation
  - name: >
      Revive dropped public access server 'testserver' with data encryption enabled as a new server 'testserverNew' with data encryption.
    text: >
      az postgres flexible-server revive-dropped -l testLocation --resource-group testGroup --name testserverNew \\
        --source-server testserver --key newKeyIdentifier --identity newIdentity
"""

helps['postgres flexible-server upgrade'] = """
type: command
short-summary: Upgrade the major version of a flexible server.
examples:
  - name: Upgrade server 'testsvr' to PostgreSQL major version 18.
    text: az postgres flexible-server upgrade -g testgroup -n testsvr -v 18
"""

helps['postgres flexible-server identity'] = """
type: group
short-summary: Manage server user assigned identities.
"""

helps['postgres flexible-server identity update'] = """
type: command
short-summary: Update to enable or disable system assigned managed identity on the server.
examples:
  - name: Enable system assigned managed identity on the server.
    text: az postgres flexible-server identity update -g testgroup -s testsvr --system-assigned Enabled
"""

helps['postgres flexible-server identity assign'] = """
type: command
short-summary: Add user assigned managed identities to the server.
examples:
  - name: Add identities 'test-identity' and 'test-identity-2' to server 'testsvr'.
    text: az postgres flexible-server identity assign -g testgroup -s testsvr --identity test-identity test-identity-2
"""

helps['postgres flexible-server identity remove'] = """
type: command
short-summary: Remove user assigned managed identites from the server.
examples:
  - name: Remove identity 'test-identity' from server 'testsvr'.
    text: az postgres flexible-server identity remove -g testgroup -s testsvr --identity test-identity
"""

helps['postgres flexible-server identity show'] = """
type: command
short-summary: Get an user assigned managed identity from the server.
examples:
  - name: Get identity 'test-identity' from server 'testsvr'.
    text: az postgres flexible-server identity show -g testgroup -s testsvr --identity test-identity
"""

helps['postgres flexible-server identity list'] = """
type: command
short-summary: List all user assigned managed identities from the server.
examples:
  - name: List all identities from server 'testsvr'.
    text: az postgres flexible-server identity list -g testgroup -s testsvr
"""

helps['postgres flexible-server microsoft-entra-admin'] = """
type: group
short-summary: Manage server Microsoft Entra administrators.
"""

helps['postgres flexible-server microsoft-entra-admin create'] = """
type: command
short-summary: Create a Microsoft Entra administrator.
examples:
  - name: Create Microsoft Entra administrator with user 'john@contoso.com', administrator ID '00000000-0000-0000-0000-000000000000' and type User.
    text: az postgres flexible-server microsoft-entra-admin create -g testgroup -s testsvr -u john@contoso.com -i 00000000-0000-0000-0000-000000000000 -t User
"""

helps['postgres flexible-server microsoft-entra-admin delete'] = """
type: command
short-summary: Delete a Microsoft Entra administrator.
examples:
  - name: Delete Microsoft Entra administrator with ID '00000000-0000-0000-0000-000000000000'.
    text: az postgres flexible-server microsoft-entra-admin delete -g testgroup -s testsvr -i 00000000-0000-0000-0000-000000000000
"""

helps['postgres flexible-server microsoft-entra-admin list'] = """
type: command
short-summary: List all Microsoft Entra administrators.
examples:
  - name: List Microsoft Entra administrators.
    text: az postgres flexible-server microsoft-entra-admin list -g testgroup -s testsvr
"""

helps['postgres flexible-server microsoft-entra-admin show'] = """
type: command
short-summary: Get a Microsoft Entra administrator.
examples:
  - name: Get Microsoft Entra administrator with ID '00000000-0000-0000-0000-000000000000'.
    text: az postgres flexible-server microsoft-entra-admin show -g testgroup -s testsvr -i 00000000-0000-0000-0000-000000000000
"""

helps['postgres flexible-server microsoft-entra-admin wait'] = """
type: command
short-summary: Wait for a Microsoft Entra administrator to satisfy certain conditions.
examples:
  - name: Wait until a Microsoft Entra administrator exists.
    text: az postgres flexible-server microsoft-entra-admin wait -g testgroup -s testsvr -i 00000000-0000-0000-0000-000000000000 --exists
  - name: Wait for a Microsoft Entra administrator to be deleted.
    text: az postgres flexible-server microsoft-entra-admin wait -g testgroup -s testsvr -i 00000000-0000-0000-0000-000000000000 --deleted
"""

helps['postgres flexible-server advanced-threat-protection-setting'] = """
type: group
short-summary: Manage advanced threat protection setting for a PostgreSQL flexible server.
"""

helps['postgres flexible-server advanced-threat-protection-setting update'] = """
type: command
short-summary: Updates advanced threat protection setting state for a flexible server.
examples:
  - name: >
      Enable advanced threat protection setting for a PostgreSQL flexible server.
    text: >
      az postgres flexible-server advanced-threat-protection-setting update --resource-group testGroup --server-name testserver --state Enabled
  - name: >
      Disable advanced threat protection setting for a PostgreSQL flexible server.
    text: >
      az postgres flexible-server advanced-threat-protection-setting update --resource-group testGroup --server-name testserver --state Disabled
"""

helps['postgres flexible-server advanced-threat-protection-setting show'] = """
type: command
short-summary: Get advanced threat protection settings for a PostgreSL flexible server.
examples:
  - name: Get the details of advanced threat protection setting for a flexible server.
    text: az postgres flexible-server advanced-threat-protection-setting show --resource-group testGroup --server-name testserver
  - name: Get the details of advanced threat protection setting for a flexible server in a different subscription.
    text: az postgres flexible-server advanced-threat-protection-setting show --subscription testSubscription --resource-group testGroup --server-name testserver
  - name: Get the details of advanced threat protection setting for a flexible server using --ids parameter.
    text: az postgres flexible-server advanced-threat-protection-setting show --ids /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/testGroup/providers/Microsoft.DBforPostgreSQL/flexibleServers/testServer
"""

helps['postgres flexible-server server-logs'] = """
type: group
short-summary: Manage server logs (log files) for a PostgreSQL flexible server.
"""

helps['postgres flexible-server server-logs download'] = """
type: command
short-summary: Download log files for a PostgreSQL flexible server.
examples:
  - name: >
      Downloads log files f1 and f2 to the current directory from the server 'testsvr'. Please note that f1 and f2 should match the log file name including the foldername, for instance serverlogs/f1.log
    text: >
      az postgres flexible-server server-logs download -g testgroup -s testsvr -n serverlogs/f1.log serverlogs/f2.log
"""

helps['postgres flexible-server server-logs list'] = """
type: command
short-summary: List log files for a PostgreSQL flexible server.
examples:
  - name: List log files for 'testsvr' modified in the last 72 hours (default value).
    text: az postgres flexible-server server-logs list -g testgroup -s testsvr
  - name: List log files for 'testsvr' modified in the last 10 hours.
    text: az postgres flexible-server server-logs list -g testgroup -s testsvr --file-last-written 10
  - name: List log files for 'testsvr' less than 30Kb in size.
    text: az postgres flexible-server server-logs list -g testgroup -s testsvr --max-file-size 30
  - name: List log files for 'testsvr' containing name 'serverlogs'.
    text: az postgres flexible-server server-logs list -g testgroup -s testsvr --subscription testSubscription --filename-contains serverlogs
"""

helps['postgres flexible-server private-endpoint-connection'] = """
type: group
short-summary: Manage PostgreSQL flexible server private endpoint connections.
"""

helps['postgres flexible-server private-endpoint-connection list'] = """
type: command
short-summary: List all private endpoint connections associated with a PostgreSQL flexible server.
examples:
  - name: List all private endpoint connections associated with a PostgreSQL flexible server.
    text: az postgres flexible-server private-endpoint-connection list -g testgroup -s testsvr
"""

helps['postgres flexible-server private-endpoint-connection show'] = """
type: command
short-summary: Show details of a private endpoint connection associated with a PostgreSQL flexible server.
examples:
  - name: Show details of a private endpoint connection associated with a PostgreSQL flexible server.
    text: az postgres flexible-server private-endpoint-connection show -g testgroup -s testsvr -n pec-connection.40e3d3a8-7d8f-41eb-8462-1cd05bc3e33b
"""

helps['postgres flexible-server private-endpoint-connection approve'] = """
type: command
short-summary: Approve the specified private endpoint connection associated with a PostgreSQL flexible server.
examples:
  - name: Approve a private endpoint connection associated with a PostgreSQL flexible server.
    text: >
      az postgres flexible-server private-endpoint-connection approve -g testgroup -s testsvr \
        -n pec-connection.40e3d3a8-7d8f-41eb-8462-1cd05bc3e33b \
        --description "Approve connection"
"""

helps['postgres flexible-server private-endpoint-connection reject'] = """
type: command
short-summary: Reject the specified private endpoint connection associated with a PostgreSQL flexible server.
examples:
  - name: Reject a private endpoint connection associated with a PostgreSQL flexible server.
    text: >
      az postgres flexible-server private-endpoint-connection reject -g testgroup -s testsvr \
        -n pec-connection.40e3d3a8-7d8f-41eb-8462-1cd05bc3e33b \
        --description "Reject connection"
"""

helps['postgres flexible-server private-endpoint-connection delete'] = """
type: command
short-summary: Delete the specified private endpoint connection associated with a PostgreSQL flexible server.
examples:
  - name: Delete a private endpoint connection associated with a PostgreSQL flexible server.
    text: >
      az postgres flexible-server private-endpoint-connection delete -g testgroup -s testsvr \
        --id /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/testgroup/providers/Microsoft.DBforPostgreSQL/flexibleServers/testsvr/privateEndpointConnections/pec-connection.40e3d3a8-7d8f-41eb-8462-1cd05bc3e33b
"""

helps['postgres flexible-server private-link-resource'] = """
type: group
short-summary: Get Private link resource for a PostgreSQL flexible server.
"""

helps['postgres flexible-server private-link-resource list'] = """
type: command
short-summary: List private link resources associated with a PostgreSQL flexible server.
examples:
  - name: List private link resources associated with a PostgreSQL flexible server.
    text: az postgres flexible-server private-link-resource list -g testgroup -s testsvr
"""

helps['postgres flexible-server private-link-resource show'] = """
type: command
short-summary: Get private link  resource for a PostgreSQL flexible server.
examples:
  - name: Get the private link  resource for a flexible server.
    text: az postgres flexible-server private-link-resource show --resource-group testGroup --server-name testserver
  - name: Get the private link  resource for a flexible server in a different subscription.
    text: az postgres flexible-server private-link-resource show --subscription testSubscription --resource-group testGroup --server-name testserver
  - name: Get the private link resource for a flexible server using --ids parameter.
    text: az postgres flexible-server private-link-resource show --ids /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/testGroup/providers/Microsoft.DBforPostgreSQL/flexibleServers/testServer
"""

helps['postgres flexible-server fabric-mirroring'] = """
type: group
short-summary: Bring your PostgreSQL data into Microsoft Fabric. Mirroring allows you to create a replica of your data in OneLake which can be used for all your analytical needs.
"""

helps['postgres flexible-server fabric-mirroring start'] = """
type: command
short-summary: Enable bringing your PostgreSQL data into Microsoft Fabric.
examples:
  - name: Enable bringing your PostgreSQL data into Microsoft Fabric.
    text: az postgres flexible-server fabric-mirroring start -g testgroup -s testsvr --database-names testdb
"""

helps['postgres flexible-server fabric-mirroring stop'] = """
type: command
short-summary: Stop bringing your PostgreSQL data into Microsoft Fabric.
examples:
  - name: Stop bringing your PostgreSQL data into Microsoft Fabric.
    text: az postgres flexible-server fabric-mirroring stop -g testgroup -s testsvr
"""

helps['postgres flexible-server fabric-mirroring update-databases'] = """
type: command
short-summary: Update allowed mirrored databases.
examples:
  - name: Update allowed mirrored databases.
    text: az postgres flexible-server fabric-mirroring update-databases -g testgroup -s testsvr --database-names testdb2 testdb3
"""

helps['postgres flexible-server index-tuning'] = """
type: group
short-summary: Index tuning analyzes read queries captured in Query Store and recommends index changes to optimize these queries.
"""

helps['postgres flexible-server index-tuning update'] = """
type: command
short-summary: Update index tuning to be enabled/disabled for a PostgreSQL flexible server.
examples:
  - name: Update index tuning to be enabled/disabled for a PostgreSQL flexible server.
    text: az postgres flexible-server index-tuning update -g testgroup -s testsvr --enabled True
"""

helps['postgres flexible-server index-tuning show'] = """
type: command
short-summary: Show state of index tuning for a PostgreSQL flexible server.
examples:
  - name: Show state of index tuning for a PostgreSQL flexible server.
    text: az postgres flexible-server index-tuning show -g testgroup -s testsvr
"""

helps['postgres flexible-server index-tuning list-settings'] = """
type: command
short-summary: Get tuning settings associated for a PostgreSQL flexible server.
examples:
  - name: Get tuning settings for a PostgreSQL flexible server.
    text: az postgres flexible-server index-tuning list-settings -g testgroup -s testsvr
"""

helps['postgres flexible-server index-tuning show-settings'] = """
type: command
short-summary: Get a tuning setting for a PostgreSQL flexible server.
examples:
  - name: Get a tuning setting for a PostgreSQL flexible server.
    text: az postgres flexible-server index-tuning show-settings -g testgroup -s testsvr --name setting-name
"""

helps['postgres flexible-server index-tuning set-settings'] = """
type: command
short-summary: Update a tuning setting for a PostgreSQL flexible server.
examples:
  - name: Update a tuning setting for a PostgreSQL flexible server.
    text: az postgres flexible-server index-tuning set-settings -g testgroup -s testsvr --name setting-name --value setting-value
"""

helps['postgres flexible-server index-tuning list-recommendations'] = """
type: command
short-summary: Get available tuning index recommendations associated with a PostgreSQL flexible server.
examples:
  - name: Get tuning index recommendations for a PostgreSQL flexible server. Filter by selected type.
    text: az postgres flexible-server index-tuning list-recommendations -g testgroup -s testsvr --recommendation-type CreateIndex
"""

helps['postgres flexible-server autonomous-tuning'] = """
type: group
short-summary: Autonomous tuning analyzes read queries captured in query store and recommends operations on tables or index changes to optimize these queries.
"""

helps['postgres flexible-server autonomous-tuning update'] = """
type: command
short-summary: Update autonomous tuning to be enabled/disabled for a PostgreSQL flexible server.
examples:
  - name: Update autonomous tuning to be enabled for a PostgreSQL flexible server.
    text: az postgres flexible-server autonomous-tuning update -g testgroup -s testsvr --enabled True
  - name: Update autonomous tuning to be disabled for a PostgreSQL flexible server.
    text: az postgres flexible-server autonomous-tuning update -g testgroup -s testsvr --enabled False
"""

helps['postgres flexible-server autonomous-tuning show'] = """
type: command
short-summary: Show state of autonomous tuning for a PostgreSQL flexible server.
examples:
  - name: Show state of autonomous tuning for a PostgreSQL flexible server.
    text: az postgres flexible-server autonomous-tuning show -g testgroup -s testsvr
"""

helps['postgres flexible-server autonomous-tuning list-settings'] = """
type: command
short-summary: Get autonomous tuning settings associated to a PostgreSQL flexible server.
examples:
  - name: Get autonomous tuning settings for a PostgreSQL flexible server.
    text: az postgres flexible-server autonomous-tuning list-settings -g testgroup -s testsvr
"""

helps['postgres flexible-server autonomous-tuning show-settings'] = """
type: command
short-summary: Get an autonomous tuning setting for a PostgreSQL flexible server.
examples:
  - name: Get an autonomous tuning setting for a PostgreSQL flexible server.
    text: az postgres flexible-server autonomous-tuning show-settings -g testgroup -s testsvr --name setting-name
"""

helps['postgres flexible-server autonomous-tuning set-settings'] = """
type: command
short-summary: Update an autonomous tuning setting for a PostgreSQL flexible server.
examples:
  - name: Update an autonomous tuning setting for a PostgreSQL flexible server.
    text: az postgres flexible-server autonomous-tuning set-settings -g testgroup -s testsvr --name setting-name --value setting-value
"""

helps['postgres flexible-server autonomous-tuning list-index-recommendations'] = """
type: command
short-summary: Get available autonomous tuning index recommendations associated with a PostgreSQL flexible server.
examples:
  - name: Get autonomous tuning index recommendations for a PostgreSQL flexible server. Filter by selected type.
    text: az postgres flexible-server autonomous-tuning list-index-recommendations -g testgroup -s testsvr --recommendation-type CreateIndex
"""

helps['postgres flexible-server autonomous-tuning list-table-recommendations'] = """
type: command
short-summary: Get available autonomous tuning table recommendations associated with a PostgreSQL flexible server.
examples:
  - name: Get autonomous tuning table recommendations for a PostgreSQL flexible server. Filter by selected type.
    text: az postgres flexible-server autonomous-tuning list-table-recommendations -g testgroup -s testsvr --recommendation-type AnalyzeTable
"""
