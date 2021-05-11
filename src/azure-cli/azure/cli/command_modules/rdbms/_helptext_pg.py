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
short-summary: Create a flexible server.
examples:
  - name: Create a PostgreSQL flexible server with default params ( resource group, location, servername, username, password ) with VNET enabled by default.
    text: |
        az postgres flexible-server create

  - name: Create a PostgreSQL flexible server with default params ( resource group, location, servername, username, password ) with all public IPs(0.0.0.0 - 255.255.255.255).
    text: |
        az postgres flexible-server create --public-access all

  - name: Create a PostgreSQL flexible server with default params ( resource group, location, servername, username, password ) with public access without any firewall rules.
    text: |
        az postgres flexible-server create --public-access none
  - name: Create a PostgreSQL flexible server with public access and add client IP address to have access to the server
    text: |
      az postgres flexible-server create --public-access <my_client_ip>
  - name: Create a PostgreSQL flexible server with public access and add the range of IP address to have access to this server
    text: |
      az postgres flexible-server create --public-access <start_ip_address-end_ip_address>
  - name: Create a PostgreSQL flexible server with public access and allow applications from Azure IP addresses to connect to your flexible server
    text: |
      az postgres flexible-server create --public-access 0.0.0.0
  - name: Create a PostgreSQL flexible server with specified SKU and storage, using defaults from local context.
    text: |
        az postgres flexible-server create --name testServer --admin-password password
  - name: Create a PostgreSQL flexible server using already existing virtual network and subnet. If provided virtual network and subnet does not exists then virtual network and subnet with default address prefix will be created.
    text: |
      az postgres flexible-server create --vnet myVnet --subnet mySubnet
  - name: Create a PostgreSQL flexible server using already existing virtual network, subnet, and using the subnet ID. The provided subnet should not have any other resource deployed in it and this subnet will be delegated to Microsoft.DBforMySQL/flexibleServers, if not already delegated.
    text: |
      az postgres flexible-server create --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNetName}/subnets/{SubnetName}
  - name: Create a PostgreSQL flexible server using new virtual network, subnet with non-default address prefix.
    text: |
      az postgres flexible-server create --vnet myVnet --address-prefixes 15.0.0.0/24 --subnet mySubnet --subnet-prefixes 15.0.0.0/24
  - name: Create a PostgreSQL flexible server using new virtual network, subnet, and new private dns zone address
    text: |
      az postgres flexible-server create --vnet myVnet --subnet mySubnet --private-dns-zone myDnsZone.private.postgres.database.azure.com
  - name: Create a PostgreSQL flexible server using existing subnet and private dns zone address in different resource group
    text: |
      az postgres flexible-server create --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNetName}/subnets/{SubnetName} --private-dns-zone /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/privateDnsZones/myDnsZone.private.postgres.database.azure.com
  - name: Create a PostgreSQL flexible server with  parameters set.
    text: |
        az postgres flexible-server create --location northeurope --resource-group testGroup \\
          --name testServer --admin-user username --admin-password password \\
          --sku-name Standard_D4s_v3 --tier GeneralPurpose --public-access 0.0.0.0 \\
          --storage-size 512 --tags "key=value" --version 12
"""

helps['postgres flexible-server delete'] = """
type: command
short-summary: Delete a flexible server.
examples:
  - name: Delete a flexible server.
    text: az postgres flexible-server delete --resource-group testGroup --name testServer
  - name: Delete a flexible server without prompt or confirmation.
    text: az postgres flexible-server delete --resource-group testGroup --name testServer --yes
"""

helps['postgres flexible-server db'] = """
type: group
short-summary: Manage PostgreSQL databases on a flexible server.
"""

helps['postgres flexible-server db create'] = """
type: command
short-summary: Create a PostgreSQL database on a flexible server.
examples:
  - name: Create database 'testDatabase' in the flexible server 'testServer' with the default parameters.
    text: az postgres flexible-server db create --resource-group testGroup --server-name testServer --database-name testDatabase
  - name: Create database 'testDatabase' in the flexible server 'testServer' with a given character set and collation rules.
    text: az postgres flexible-server db create --resource-group testGroup --server-name testServer --database-name testDatabase \\
            --charset validCharset --collation validCollation
"""

helps['postgres flexible-server db delete'] = """
type: command
short-summary: Delete a database on a flexible server.
examples:
  - name: Delete database 'testDatabase' in the flexible server 'testServer'.
    text: az postgres flexible-server db delete --resource-group testGroup --server-name testServer --database-name testDatabase
"""

helps['postgres flexible-server db list'] = """
type: command
short-summary: List the databases for a flexible server.
examples:
  - name: List databases in the flexible server 'testServer'.
    text: az postgres flexible-server db list --resource-group testGroup --server-name testServer
"""

helps['postgres flexible-server db show'] = """
type: command
short-summary: Show the details of a database.
examples:
  - name: Show database 'testDatabase' in the server 'testServer'.
    text: az postgres flexible-server db show --resource-group testGroup --server-name testServer --database-name testDatabase
"""

helps['postgres flexible-server firewall-rule'] = """
type: group
short-summary: Manage firewall rules for a server.
"""

helps['postgres flexible-server firewall-rule create'] = """
type: command
short-summary: Create a new firewall rule for a flexible server.
examples:
  - name: Create a firewall rule allowing connections from a specific IP address.
    text: az postgres flexible-server firewall-rule create --resource-group testGroup --name testServer --rule-name allowip --start-ip-address 107.46.14.221 --end-ip-address 107.46.14.221
  - name: Create a firewall rule allowing connections from an IP address range.
    text: az postgres flexible-server firewall-rule create --resource-group testGroup --name testServer --rule-name allowiprange --start-ip-address 107.46.14.0 --end-ip-address 107.46.14.221
"""

helps['postgres flexible-server firewall-rule delete'] = """
type: command
short-summary: Delete a firewall rule.
examples:
  - name: Delete a firewall rule.
    text: az postgres flexible-server firewall-rule delete --rule-name testRule --resource-group testGroup --name testServer
    crafted: true
"""

helps['postgres flexible-server firewall-rule list'] = """
type: command
short-summary: List all firewall rules for a flexible server.
example:
  - name: List all firewall rules for a server.
    text: az postgres server firewall-rule list --resource-group testGroup --name testServer
    crafted: true
"""

helps['postgres flexible-server firewall-rule show'] = """
type: command
short-summary: Get the details of a firewall rule.
examples:
  - name: Get the details of a firewall rule.
    text: az postgres flexible-server firewall-rule show --rule-name testRule --resource-group testGroup --name testServer
    crafted: true
"""

helps['postgres flexible-server firewall-rule update'] = """
type: command
short-summary: Update a firewall rule.
examples:
  - name: Update a firewall rule's start IP address.
    text: az postgres flexible-server firewall-rule update --resource-group testGroup --name testServer --rule-name allowiprange --start-ip-address 107.46.14.1
  - name: Update a firewall rule's start and end IP address.
    text: az postgres flexible-server firewall-rule update --resource-group testGroup --name testServer --rule-name allowiprange --start-ip-address 107.46.14.2 --end-ip-address 107.46.14.218
"""

helps['postgres flexible-server list'] = """
type: command
short-summary: List available flexible servers.
examples:
  - name: List all PostgreSQL flexible servers in a subscription.
    text: az postgres flexible-server list
  - name: List all PostgreSQL flexible servers in a resource group.
    text: az postgres flexible-server list --resource-group testGroup
"""

helps['postgres flexible-server parameter'] = """
type: group
short-summary: Commands for managing server parameter values for flexible server.
example:
  - name: List the parameter values for a flexible server.
    text: az postgres flexible-server parameter list
    crafted: true
"""

helps['postgres flexible-server parameter list'] = """
type: command
short-summary: List the parameter values for a flexible server.
examples:
  - name: List the parameter values for a flexible server.
    text: az postgres flexible-server parameter list --resource-group testGroup --server-name servername
    crafted: true
"""

helps['postgres flexible-server parameter set'] = """
type: command
short-summary: Update the parameter of a flexible server.
examples:
  - name: Set a new parameter value.
    text: az postgres flexible-server parameter set --name parameterName --value parameterValue
  - name: Set a parameter value to its default.
    text: az postgres flexible-server parameter set --name parameterName
"""

helps['postgres flexible-server parameter show'] = """
type: command
short-summary: Get the parameter for a flexible server."
examples:
  - name: Get the parameter for a server.W
    text: az postgres flexible-server parameter show --name parameterName
    crafted: true
"""

helps['postgres flexible-server restart'] = """
type: command
short-summary: Restart a flexible server.
examples:
  - name: Restart a flexible server.
    text: az postgres flexible-server restart --resource-group testGroup --name testServer
    crafted: true
"""

helps['postgres flexible-server restore'] = """
type: command
short-summary: Restore a flexible server from backup.
examples:
  - name: Restore 'testServer' to a specific point-in-time as a new server 'testServerNew'.
    text: az postgres flexible-server restore --resource-group testGroup --name testServerNew --source-server testServer --restore-time "2017-06-15T13:10:00Z"
  - name: Restore 'testServer2' to 'testServerNew', where 'testServerNew' is in a different resource group from 'testServer2'.
    text: |
        az postgres flexible-server restore --resource-group testGroup --name testServerNew \\
          --source-server "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforPostgreSQL/servers/testServer2" \\
          --restore-time "2017-06-15T13:10:00Z"
"""

helps['postgres flexible-server show'] = """
type: command
short-summary: Get the details of a flexible server.
examples:
  - name: Get the details of a flexible server
    text: az postgres flexible-server show --resource-group testGroup --name testServer
    crafted: true
"""

helps['postgres flexible-server start'] = """
type: command
short-summary: Start a flexible server.
examples:
  - name: Start a flexible server.
    text: az postgres flexible-server start --resource-group testGroup --name testServer
    crafted: true
"""

helps['postgres flexible-server stop'] = """
type: command
short-summary: Stop a flexible server.
examples:
  - name: Stop a flexible server.
    text: az postgres flexible-server stop --resource-group testGroup --name testServer
    crafted: true
"""

helps['postgres flexible-server update'] = """
type: command
short-summary: Update a flexible server.
examples:
  - name: Update a flexible server's sku, using local context for server and resource group.
    text: az postgres flexible-server update --sku-name Standard_D4s_v3
  - name: Update a server's tags.
    text: az postgres flexible-server update --resource-group testGroup --name testServer --tags "k1=v1" "k2=v2"
  - name: Reset password
    text: az postgres flexible-server update --resource-group testGroup --name testServer -p password123
    crafted: true
"""

helps['postgres flexible-server list-skus'] = """
type: command
short-summary: Lists available sku's in the given region.
example:
  - name: Lists available sku's in the given region.
    text: az postgres flexible-server list-skus -l eastus
"""

helps['postgres flexible-server wait'] = """
type: command
short-summary: Wait for the flexible server to satisfy certain conditions.
example:
  - name: Wait for the flexible server to satisfy certain conditions.
    text: az postgres server wait --exists --resource-group testGroup --name testServer
    crafted: true
"""

helps['postgres flexible-server show-connection-string'] = """
type: command
short-summary: Show the connection strings for a PostgreSQL flexible-server database.
examples:
  - name: Show connection strings for cmd and programming languages.
    text: az postgres flexible-server show-connection-string -s testServer -u username -p password -d databasename
"""
