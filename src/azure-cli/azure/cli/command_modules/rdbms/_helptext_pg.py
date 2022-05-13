# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import

# pylint: disable=line-too-long, too-many-lines


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

    https://docs.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-manage-firewall-cli

    - Configure private access

    https://docs.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-manage-virtual-network-cli

examples:
  - name: >
      Create a PostgreSQL flexible server with custom parameters
    text: >
        az postgres flexible-server create --location northeurope --resource-group testGroup \\
          --name testserver --admin-user username --admin-password password \\
          --sku-name Standard_B1ms --tier Burstable --public-access 153.24.26.117 --storage-size 128 \\
          --tags "key=value" --version 13 --high-availability Enabled --zone 1 \\
          --standby-zone 3
  - name: >
      Create a PostgreSQL flexible server with default parameters and public access enabled by default. \
      Resource group, server name, username, password, and default database will be created by CLI
    text: >
        az postgres flexible-server create
  - name: >
      Create a PostgreSQL flexible server with public access and add the range of IP address to have access to this server.
      The --public-access parameter can be 'All', 'None', <startIpAddress>, or <startIpAddress>-<endIpAddress>
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
"""

helps['postgres flexible-server restore'] = """
type: command
short-summary: Restore a flexible server from backup.
examples:
  - name: Restore 'testserver' to a specific point-in-time as a new server 'testserverNew'.
    text: az postgres flexible-server restore --resource-group testGroup --name testserverNew --source-server testserver --restore-time "2017-06-15T13:10:00Z"
  - name: Restore 'testserver2' to 'testserverNew', where 'testserverNew' is in a different resource group from 'testserver2'.
    text: |
        az postgres flexible-server restore --resource-group testGroup --name testserverNew \\
          --source-server "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforPostgreSQL/servers/testserver2" \\
          --restore-time "2017-06-15T13:10:00Z"
  - name: Restore 'testserver' to current point-in-time as a new server 'testserverNew'.
    text: az postgres flexible-server restore --resource-group testGroup --name testserverNew --source-server testserver
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
    text: az postgres server wait --exists --resource-group testGroup --name testserver
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
      az postgres flexible-server firewall-rule create --resource-group testGroup --name testserver --start-ip-address 0.0.0.0
"""

helps['postgres flexible-server firewall-rule list'] = """
type: command
short-summary: List all firewall rules for a flexible server.
example:
  - name: List all firewall rules for a server.
    text: az postgres server firewall-rule list --resource-group testGroup --name testserver
  - name: List all firewall rules for a server in table format.
    text: az postgres server firewall-rule list --resource-group testGroup --name testserver --output table
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

helps['postgres flexible-server migration'] = """
type: group
short-summary: Manage migration workflows for PostgreSQL Flexible Servers.
"""

helps['postgres flexible-server migration create'] = """
type: command
short-summary: Create a new migration workflow for a flexible server.
examples:
  - name: Start a migration workflow on the target server identified by the parameters. The configurations of the migration should be specified in the migrationConfig.json file.
    text: az postgres flexible-server migration create --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --properties "migrationConfig.json"
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
    text: az postgres flexible-server migration show --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
"""

helps['postgres flexible-server migration update'] = """
type: command
short-summary: Update a specific migration.
examples:
  - name: Allow the migration workflow to setup logical replication on the source. Note that this command will restart the source server.
    text: az postgres flexible-server migration update --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --setup-replication
  - name: Space-separated list of DBs to migrate. A minimum of 1 and a maximum of 8 DBs can be specified. You can migrate more DBs concurrently using additional migrations. Note that each additional DB affects the performance of the source server.
    text: az postgres flexible-server migration update --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --db-names db1 db2
  - name: Allow the migration workflow to overwrite the DB on the target.
    text: az postgres flexible-server migration update --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --overwrite-dbs
  - name: This command helps in starting the data migration immediately between the source and target. Any migration scheduled for a future date and time will be cancelled.
    text: az postgres flexible-server migration update --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --start-data-migration
"""

helps['postgres flexible-server migration delete'] = """
type: command
short-summary: Delete a specific migration.
examples:
  - name: Cancel/delete the migration workflow. The migration workflows can be canceled/deleted at any point.
    text: az postgres flexible-server migration delete --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --resource-group testGroup --name testserver --migration-name xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
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
  - name: Get the parameter for a server.W
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
"""

helps['postgres flexible-server deploy'] = """
type: group
short-summary: Enable and run github action workflow for PostgreSQL server
"""

helps['postgres flexible-server deploy setup'] = """
type: command
short-summary: Create github action workflow file for PostgreSQL server.
examples:
  - name: Create github action workflow file for PostgreSQL server.
    text: az postgres flexible-server deploy setup -s testserver -g testGroup -u username -p password --sql-file test.sql --repo username/userRepo -d flexibleserverdb --action-name testAction
  - name: Create github action workflow file for PostgreSQL server and push it to the remote repository
    text: az postgres flexible-server deploy setup -s testserver -g testGroup -u username -p password --sql-file test.sql --repo username/userRepo -d flexibleserverdb --action-name testAction --branch userBranch --allow-push
"""

helps['postgres flexible-server deploy run'] = """
type: command
short-summary: Run an existing workflow in your github repository
examples:
  - name: Run an existing workflow in your github repository
    text: az postgres flexible-server deploy run --action-name testAction --branch userBranch
"""
