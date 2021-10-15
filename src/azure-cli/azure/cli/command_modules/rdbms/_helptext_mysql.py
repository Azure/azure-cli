# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['mysql flexible-server'] = """
type: group
short-summary: Manage Azure Database for MySQL Flexible Servers.
"""

helps['mysql flexible-server create'] = """
type: command
short-summary: Create a MySQL flexible server.
long-summary: >
    Create a MySQL flexible server with custom or default configuration. For more information for network configuration, see

    - Configure public access

    https://docs.microsoft.com/en-us/azure/mysql/flexible-server/how-to-manage-firewall-cli

    - Configure private access

    https://docs.microsoft.com/en-us/azure/mysql/flexible-server/how-to-manage-virtual-network-cli

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
examples:
  - name: Update a flexible server's sku, using local context for server and resource group.
    text: az mysql flexible-server update --sku-name Standard_D4ds_v4 --tier GeneralPurpose
  - name: Update a flexible server's tags.
    text: az mysql flexible-server update --resource-group testGroup --name testserver --tags "k1=v1" "k2=v2"
    crafted: true
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
      Geo-estore public access or private access server 'testserver' as a new server 'testserverNew' with new subnet.
      New vnet, subnet, and private dns zone for the restored server will be provisioned. Please refer to 'flexible-server create' command for more private access scenarios.
    text: >
      az mysql flexible-server geo-restore --resource-group testGroup --name testserverNew \\
        --source-server testserver --vnet newVnet --subnet newSubnet \\
        --address-prefixes 172.0.0.0/16 --subnet-prefixes 172.0.0.0/24 \\
        --private-dns-zone testDNS.mysql.database.azure.com --location newLocation
  - name: Gep-estore private access server 'testserver' as a new server 'testserverNew' with public access.
    text: >
      az mysql flexible-server geo-restore --resource-group testGroup --name testserverNew  --source-server testserver --public-access Enabled --location newLocation
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
"""

helps['mysql flexible-server replica list'] = """
type: command
short-summary: List all read replicas for a given server.
examples:
  - name: List all read replicas for master server 'testserver'.
    text: az mysql flexible-server replica list -g testGroup -n primaryservername
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
short-summary: Enable and run github action workflow for MySQL server
"""

helps['mysql flexible-server deploy setup'] = """
type: command
short-summary: Create github action workflow file for MySQL server.
examples:
  - name: Create github action workflow file for MySQL server.
    text: az mysql flexible-server deploy setup -s testserver -g testGroup -u username -p password --sql-file test.sql --repo username/userRepo -d flexibleserverdb --action-name testAction
  - name: Create github action workflow file for MySQL server and push it to the remote repository
    text: az mysql flexible-server deploy setup -s testserver -g testGroup -u username -p password --sql-file test.sql --repo username/userRepo -d flexibleserverdb --action-name testAction --branch userBranch --allow-push
"""

helps['mysql flexible-server deploy run'] = """
type: command
short-summary: Run an existing workflow in your github repository
examples:
  - name: Run an existing workflow in your github repository
    text: az mysql flexible-server deploy run --action-name testAction --branch userBranch
"""
