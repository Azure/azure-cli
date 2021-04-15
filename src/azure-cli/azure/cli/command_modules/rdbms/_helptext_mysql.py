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
short-summary: Create a flexible server.
examples:
  - name: Create a MySQL flexible server with default params (resource group, location, servername, username, password) with VNET enabled by default.
    text: |
        az mysql flexible-server create
  - name: Create a MySQL flexible server with default params (resource group, location, servername, username, password) with all public IPs (0.0.0.0 - 255.255.255.255).
    text: |
        az mysql flexible-server create --public-access all
  - name: Create a MySQL flexible server with default params ( resource group, location, servername, username, password ) with public access without any firewall rules.
    text: |
        az mysql flexible-server create --public-access none
  - name: Create a MySQL flexible server with public access and add client IP address to have access to the server
    text: |
        az mysql flexible-server create --public-access <my_client_ip>
  - name: Create a MySQL flexible server with public access and add the range of IP address to have access to this server
    text: |
      az mysql flexible-server create --public-access <start_ip_address-end_ip_address>
  - name: Create a MySQL flexible server with public access and allow applications from Azure IP addresses to connect to your flexible server
    text: |
      az mysql flexible-server create --public-access 0.0.0.0
  - name: Create a MySQL flexible server with specified SKU and storage, using defaults from local context.
    text: |
        az mysql flexible-server create --name testServer --admin-password password
  - name: Create a MySQL flexible server using already existing virtual network and subnet. If provided virtual network and subnet does not exists then virtual network and subnet with default address prefix will be created.
    text: |
      az mysql flexible-server create --vnet myVnet --subnet mySubnet
  - name: Create a MySQL flexible server using already existing virtual network, subnet, and using the subnet ID. The provided subnet should not have any other resource deployed in it and this subnet will be delegated to Microsoft.DBforMySQL/flexibleServers, if not already delegated.
    text: |
      az mysql flexible-server create --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNetName}/subnets/{SubnetName}
  - name: Create a MySQL flexible server using new virtual network, subnet with non-default address prefix.
    text: |
      az mysql flexible-server create --vnet myVnet --address-prefixes 10.0.0.0/24 --subnet mySubnet --subnet-prefixes 10.0.0.0/24
  - name: Create a MySQL flexible server with  parameters set.
    text: |
        az mysql flexible-server create --location northeurope --resource-group testGroup \\
          --name testServer --admin-user username --admin-password password \\
          --sku-name Standard-B1ms --tier Burstable --public-access 0.0.0.0 --storage-size 32 \\
          --tags "key=value" --version 5.7
"""

helps['mysql flexible-server db'] = """
type: group
short-summary: Manage MySQL databases on a flexible server.
"""

helps['mysql flexible-server db create'] = """
type: command
short-summary: Create a MySQL database on a flexible server.
examples:
  - name: Create database 'testDatabase' in the flexible server 'testServer' with the default parameters.
    text: az mysql flexible-server db create --resource-group testGroup --server-name testServer --database-name testDatabase
  - name: Create database 'testDatabase' in the flexible server 'testServer' with a given character set and collation rules.
    text: az mysql flexible-server db create --resource-group testGroup --server-name testServer --database-name testDatabase \\
            --charset validCharset --collation validCollation
"""

helps['mysql flexible-server db delete'] = """
type: command
short-summary: Delete a database on a flexible server.
examples:
  - name: Delete database 'testDatabase' in the flexible server 'testServer'.
    text: az mysql flexible-server db delete --resource-group testGroup --server-name testServer --database-name testDatabase
"""

helps['mysql flexible-server db list'] = """
type: command
short-summary: List the databases for a flexible server.
examples:
  - name: List databases in the flexible server 'testServer'.
    text: az mysql flexible-server db list --resource-group testGroup --server-name testServer
"""

helps['mysql flexible-server db show'] = """
type: command
short-summary: Show the details of a database.
examples:
  - name: Show database 'testDatabase' in the server 'testServer'.
    text: az mysql flexible-server db show --resource-group testGroup --server-name testServer --database-name testDatabase
"""

helps['mysql flexible-server delete'] = """
type: command
short-summary: Delete a flexible server.
examples:
  - name: Delete a flexible server.
    text: az mysql flexible-server delete --resource-group testGroup --name testServer
  - name: Delete a flexible server without prompt or confirmation.
    text: az mysql flexible-server delete --resource-group testGroup --name testServer --yes
"""

helps['mysql flexible-server firewall-rule'] = """
type: group
short-summary: Manage firewall rules for a server.
"""

helps['mysql flexible-server firewall-rule create'] = """
type: command
short-summary: Create a new firewall rule for a flexible server.
examples:
  - name: Create a firewall rule allowing connections from a specific IP address.
    text: az mysql flexible-server firewall-rule create --resource-group testGroup --name testServer --rule-name allowip --start-ip-address 107.46.14.221 --end-ip-address 107.46.14.221
  - name: Create a firewall rule allowing connections from an IP address range.
    text: az mysql flexible-server firewall-rule create --resource-group testGroup --name testServer --rule-name allowiprange --start-ip-address 107.46.14.0 --end-ip-address 107.46.14.221
"""

helps['mysql flexible-server firewall-rule delete'] = """
type: command
short-summary: Delete a firewall rule.
examples:
  - name: Delete a firewall rule.
    text: az mysql flexible-server firewall-rule delete --rule-name testRule --resource-group testGroup --name testServer
    crafted: true
"""

helps['mysql flexible-server firewall-rule list'] = """
type: command
short-summary: List all firewall rules for a flexible server.
example:
  - name: List all firewall rules for a server.
    text: az mysql server firewall-rule list --resource-group testGroup --name testServer
    crafted: false
"""

helps['mysql flexible-server firewall-rule show'] = """
type: command
short-summary: Get the details of a firewall rule.
examples:
  - name: Get the details of a firewall rule.
    text: az mysql flexible-server firewall-rule show --rule-name testRule --resource-group testGroup --name testServer
    crafted: true
"""

helps['mysql flexible-server firewall-rule update'] = """
type: command
short-summary: Update a firewall rule.
examples:
  - name: Update a firewall rule's start IP address.
    text: az mysql flexible-server firewall-rule update --resource-group testGroup --name testServer \\
            --rule-name allowiprange --start-ip-address 107.46.14.1
  - name: Update a firewall rule's start and end IP address.
    text: az mysql flexible-server firewall-rule update --resource-group testGroup --name testServer \\
            --rule-name allowiprange --start-ip-address 107.46.14.2 --end-ip-address 107.46.14.218
"""

helps['mysql flexible-server list'] = """
type: command
short-summary: List available flexible servers.
examples:
  - name: List all MySQL flexible servers in a subscription.
    text: az mysql flexible-server list
  - name: List all MySQL flexible servers in a resource group.
    text: az mysql flexible-server list --resource-group testGroup
"""

helps['mysql flexible-server parameter'] = """
type: group
short-summary: Commands for managing server parameter values for flexible server.
example:
  - name: List the parameter values for a flexible server.
    text: az mysql flexible-server parameter list
    crafted: true
"""

helps['mysql flexible-server parameter list'] = """
type: command
short-summary: List the parameter values for a flexible server.
examples:
  - name: List the parameter values for a flexible server.
    text: az mysql flexible-server parameter list --resource-group testGroup --server-name servername
    crafted: true
"""

helps['mysql flexible-server parameter set'] = """
type: command
short-summary: Update the parameter of a flexible server.
examples:
  - name: Set a new parameter value.
    text: az mysql flexible-server parameter set --name parameterName --value parameterValue
  - name: Set a parameter value to its default.
    text: az mysql flexible-server parameter set --name parameterName
"""

helps['mysql flexible-server parameter show'] = """
type: command
short-summary: Get the parameter for a flexible server."
examples:
  - name: Get the parameter for a server.W
    text: az mysql flexible-server parameter show --name parameterName
    crafted: true
"""

helps['mysql flexible-server replica'] = """
type: group
short-summary: Manage read replicas.
"""

helps['mysql flexible-server replica create'] = """
type: command
short-summary: Create a read replica for a server.
examples:
  - name: Create a read replica 'testReplicaServer' for 'testServer'.
    text: az mysql flexible-server replica create --replica-name testReplicaServer -g testGroup --source-server testServer
"""

helps['mysql flexible-server replica list'] = """
type: command
short-summary: List all read replicas for a given server.
examples:
  - name: List all read replicas for master server 'testServer'.
    text: az mysql flexible-server replica list -g testGroup -n primaryservername
"""

helps['mysql flexible-server replica stop-replication'] = """
type: command
short-summary: Stop replication to a read replica and make it a read/write server.
examples:
  - name: Stop replication to 'testReplicaServer' and make it a read/write server.
    text: az mysql flexible-server replica stop-replication -g testGroup -n testReplicaServer
"""

helps['mysql flexible-server restart'] = """
type: command
short-summary: Restart a flexible server.
examples:
  - name: Restart a flexible server.
    text: az mysql flexible-server restart --resource-group testGroup --name testServer
    crafted: true
"""

helps['mysql flexible-server restore'] = """
type: command
short-summary: Restore a flexible server from backup.
examples:
  - name: Restore 'testServer' to a specific point-in-time as a new server 'testServerNew'.
    text: az mysql flexible-server restore --resource-group testGroup --name testServerNew --source-server testServer --restore-time "2017-06-15T13:10:00Z"
  - name: Restore 'testServer2' to 'testServerNew', where 'testServerNew' is in a different resource group from 'testServer2'.
    text: |
        az mysql flexible-server restore --resource-group testGroup --name testServerNew \\
          --source-server "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforMySQL/servers/testServer2" \\
          --restore-time "2017-06-15T13:10:00Z"
"""

helps['mysql flexible-server show'] = """
type: command
short-summary: Get the details of a flexible server.
examples:
  - name: Get the details of a flexible server
    text: az mysql flexible-server show --resource-group testGroup --name testServer
    crafted: true
"""

helps['mysql flexible-server start'] = """
type: command
short-summary: Start a flexible server.
examples:
  - name: Start a flexible server.
    text: az mysql flexible-server start --resource-group testGroup --name testServer
    crafted: true
"""

helps['mysql flexible-server stop'] = """
type: command
short-summary: Stop a flexible server.
examples:
  - name: Stop a flexible server.
    text: az mysql flexible-server stop --resource-group testGroup --name testServer
    crafted: true
"""

helps['mysql flexible-server update'] = """
type: command
short-summary: Update a flexible server.
examples:
  - name: Update a flexible server's sku, using local context for server and resource group.
    text: az mysql flexible-server update --sku-name Standard_D4ds_v4 --tier GeneralPurpose
  - name: Update a flexible server's tags.
    text: az mysql flexible-server update --resource-group testGroup --name testServer --tags "k1=v1" "k2=v2"
    crafted: true
"""

helps['mysql flexible-server list-skus'] = """
type: command
short-summary: Lists available sku's in the given region.
examples:
  - name: Lists available sku's in the given region.
    text: az mysql flexible-server list-skus -l eastus
"""

helps['mysql flexible-server wait'] = """
type: command
short-summary: Wait for the flexible server to satisfy certain conditions.
examples:
  - name: Wait for the flexible server to satisfy certain conditions.
    text: az mysql flexible-server wait --exists --resource-group testGroup --name testServer
    crafted: true
"""

helps['mysql flexible-server show-connection-string'] = """
type: command
short-summary: Show the connection strings for a MySQL flexible-server database.
examples:
  - name: Show connection strings for cmd and programming languages.
    text: az mysql flexible-server show-connection-string -s testServer -u username -p password -d databasename
"""
