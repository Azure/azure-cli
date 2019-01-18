# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["mariadb"] = """
type: group
short-summary: Manage Azure Database for MariaDB servers.
"""

helps["mariadb db"] = """
type: group
short-summary: Manage MariaDB databases on a server.
"""

helps["mariadb db create"] = """
type: command
short-summary: Create a MariaDB database.
examples:
-   name: Create database 'testdb' in the server 'testsvr' with the default parameters.
    text: az mariadb db create -g testgroup -s testsvr -n testdb --admin-user myadmin
        --admin-password {server_admin_password} --sku-name GP_Gen4_2 --version 5.7
-   name: Create database 'testdb' in server 'testsvr' with a given character set
        and collation rules.
    text: az mariadb db create -g testgroup -s testsvr -n testdb --charset {valid_charset}
        --collation {valid_collation} --admin-user myadmin --admin-password {server_admin_password}
        --sku-name GP_Gen4_2 --version 5.7
"""

helps["mariadb db delete"] = """
type: command
short-summary: Delete a database.
examples:
-   name: Delete database 'testdb' in the server 'testsvr'.
    text: az mariadb db delete -g testgroup -s testsvr -n testdb
"""

helps["mariadb db list"] = """
type: command
short-summary: List the databases for a server.
examples:
-   name: List databases in the server 'testsvr'.
    text: az mariadb db list -g testgroup -s testsvr
"""

helps["mariadb db show"] = """
type: command
short-summary: Show the details of a database.
examples:
-   name: Show database 'testdb' in the server 'testsvr'.
    text: az mariadb db show -g testgroup -s testsvr -n testdb
"""

helps["mariadb server"] = """
type: group
short-summary: Manage MariaDB servers.
"""

helps["mariadb server configuration"] = """
type: group
short-summary: Manage configuration values for a server.
"""

helps["mariadb server configuration list"] = """
type: command
short-summary: List the configuration values for a server.
"""

helps["mariadb server configuration set"] = """
type: command
short-summary: Update the configuration of a server.
examples:
-   name: Set a new configuration value.
    text: az mariadb server configuration set -g testgroup -s testsvr -n {config_name}
        --value {config_value}
-   name: Set a configuration value to its default.
    text: az mariadb server configuration set -g testgroup -s testsvr -n {config_name}
"""

helps["mariadb server configuration show"] = """
type: command
short-summary: Get the configuration for a server."
"""

helps["mariadb server create"] = """
type: command
short-summary: Create a server.
examples:
-   name: Create a MariaDB server with only required paramaters in North Europe.
    text: az mariadb server create -l northeurope -g testgroup -n testsvr -u username
        -p password
-   name: Create a MariaDB server with a Standard performance tier and 2 vcore in
        North Europe.
    text: az mariadb server create -l northeurope -g testgroup -n testsvr -u username
        -p password \\ --sku-name GP_Gen4_2
-   name: Create a MariaDB server with all paramaters set.
    text: az mariadb server create -l northeurope -g testgroup -n testsvr -u username
        -p password \\ --sku-name B_Gen4_2 --ssl-enforcement Disabled \\ --storage-size
        51200 --tags "key=value" --version {server-version}
"""

helps["mariadb server delete"] = """
type: command
short-summary: Delete a server.
"""

helps["mariadb server firewall-rule"] = """
type: group
short-summary: Manage firewall rules for a server.
"""

helps["mariadb server firewall-rule create"] = """
type: command
short-summary: Create a new firewall rule for a server.
examples:
-   name: Create a firewall rule allowing all connections from all IP addresses.
    text: az mariadb server firewall-rule create -g testgroup -s testsvr -n allowall
        --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255
"""

helps["mariadb server firewall-rule delete"] = """
type: command
short-summary: Delete a firewall rule.
"""

helps["mariadb server firewall-rule list"] = """
type: command
short-summary: List all firewall rules for a server.
"""

helps["mariadb server firewall-rule show"] = """
type: command
short-summary: Get the details of a firewall rule.
"""

helps["mariadb server firewall-rule update"] = """
type: command
short-summary: Update a firewall rule.
examples:
-   name: Update a firewall rule's start IP address.
    text: az mariadb server firewall-rule update -g testgroup -s testsvr -n allowall
        --start-ip-address 0.0.0.1
-   name: Update a firewall rule's start and end IP address.
    text: az mariadb server firewall-rule update -g testgroup -s testsvr -n allowall
        --start-ip-address 0.0.0.1 --end-ip-address 255.255.255.254
"""

helps["mariadb server georestore"] = """
type: command
short-summary: Georestore a server from backup.
examples:
-   name: Georestore 'testsvr' as 'testsvrnew' where 'testsvrnew' is in same resource
        group as 'testsvr'.
    text: az mariadb server georestore -g testgroup -n testsvrnew --source-server
        testsvr -l westus2
-   name: Georestore 'testsvr2' to 'testsvrnew', where 'testsvrnew' is in the different
        resource group as the original server.
    text: |
        az mariadb server georestore -g testgroup -n testsvrnew \\
            -s "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforMariaDB/servers/testsvr2"
            -l westus2 --sku-name GP_Gen4_2
"""

helps["mariadb server list"] = """
type: command
short-summary: List available servers.
examples:
-   name: List all MariaDB servers in a subscription.
    text: az mariadb server list
-   name: List all MariaDB servers in a resource group.
    text: az mariadb server list -g testgroup
"""

helps["mariadb server restore"] = """
type: command
short-summary: Restore a server from backup.
examples:
-   name: Restore 'testsvr' as 'testsvrnew'.
    text: az mariadb server restore -g testgroup -n testsvrnew --source-server testsvr
        --restore-point-in-time "2017-06-15T13:10:00Z"
-   name: Restore 'testsvr2' to 'testsvrnew', where 'testsvrnew' is in a different
        resource group than the backup.
    text: |
        az mariadb server restore -g testgroup -n testsvrnew \\
            -s "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforMariaDB/servers/testsvr2" \\
            --restore-point-in-time "2017-06-15T13:10:00Z"
"""

helps["mariadb server show"] = """
type: command
short-summary: Get the details of a server.
"""

helps["mariadb server update"] = """
type: command
short-summary: Update a server.
examples:
-   name: Update a server's sku.
    text: az mariadb server update -g testgroup -n testsvrnew --sku-name GP_Gen5_4
-   name: Update a server's tags.
    text: az mariadb server update -g testgroup -n testsvrnew --tags "k1=v1" "k2=v2"
"""

helps["mariadb server vnet-rule"] = """
type: group
short-summary: Manage a server's virtual network rules.
"""

helps["mariadb server vnet-rule create"] = """
type: command
short-summary: Create a virtual network rule to allows access to a MariaDB server.
examples:
-   name: Create a virtual network rule by providing the subnet id.
    text: az mariadb server vnet-rule create -g testgroup -s testsvr -n vnetRuleName
        --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/vnetName/subnets/subnetName
-   name: Create a vnet rule by providing the vnet and subnet name. The subnet id
        is created by taking the resource group name and subscription id of the server.
    text: az mariadb server vnet-rule create -g testgroup -s testsvr -n vnetRuleName
        --subnet subnetName --vnet-name vnetName
"""

helps["mariadb server vnet-rule update"] = """
type: command
short-summary: Update a virtual network rule.
"""

helps["mariadb server wait"] = """
type: command
short-summary: Wait for server to satisfy certain conditions.
"""

helps["mariadb server-logs"] = """
type: group
short-summary: Manage server logs.
"""

helps["mariadb server-logs download"] = """
type: command
short-summary: Download log files.
examples:
-   name: Download log files f1 and f2 to the current directory from the server 'testsvr'.
    text: az mariadb server-logs download -g testgroup -s testsvr -n f1.log f2.log
"""

helps["mariadb server-logs list"] = """
type: command
short-summary: List log files for a server.
examples:
-   name: List log files for 'testsvr' modified in the last 72 hours (default value).
    text: az mariadb server-logs list -g testgroup -s testsvr
-   name: List log files for 'testsvr' modified in the last 10 hours.
    text: az mariadb server-logs list -g testgroup -s testsvr --file-last-written
        10
-   name: List log files for 'testsvr' less than 30Kb in size.
    text: az mariadb server-logs list -g testgroup -s testsvr --max-file-size 30
"""

helps["mysql"] = """
type: group
short-summary: Manage Azure Database for MySQL servers.
"""

helps["mysql db"] = """
type: group
short-summary: Manage MySQL databases on a server.
"""

helps["mysql db create"] = """
type: command
short-summary: Create a MySQL database.
examples:
-   name: Create database 'testdb' in the server 'testsvr' with the default parameters.
    text: az mysql db create -g testgroup -s testsvr -n testdb --admin-user myadmin
        --admin-password {server_admin_password} --sku-name GP_Gen4_2 --version 5.7
-   name: Create database 'testdb' in server 'testsvr' with a given character set
        and collation rules.
    text: az mysql db create -g testgroup -s testsvr -n testdb --charset {valid_charset}
        --collation {valid_collation} --admin-user myadmin --admin-password {server_admin_password}
        --sku-name GP_Gen4_2 --version 5.7
"""

helps["mysql db delete"] = """
type: command
short-summary: Delete a database.
examples:
-   name: Delete database 'testdb' in the server 'testsvr'.
    text: az mysql db delete -g testgroup -s testsvr -n testdb
"""

helps["mysql db list"] = """
type: command
short-summary: List the databases for a server.
examples:
-   name: List databases in the server 'testsvr'.
    text: az mysql db list -g testgroup -s testsvr
"""

helps["mysql db show"] = """
type: command
short-summary: Show the details of a database.
examples:
-   name: Show database 'testdb' in the server 'testsvr'.
    text: az mysql db show -g testgroup -s testsvr -n testdb
"""

helps["mysql server"] = """
type: group
short-summary: Manage MySQL servers.
"""

helps["mysql server configuration"] = """
type: group
short-summary: Manage configuration values for a server.
"""

helps["mysql server configuration list"] = """
type: command
short-summary: List the configuration values for a server.
"""

helps["mysql server configuration set"] = """
type: command
short-summary: Update the configuration of a server.
examples:
-   name: Set a new configuration value.
    text: az mysql server configuration set -g testgroup -s testsvr -n {config_name}
        --value {config_value}
-   name: Set a configuration value to its default.
    text: az mysql server configuration set -g testgroup -s testsvr -n {config_name}
"""

helps["mysql server configuration show"] = """
type: command
short-summary: Get the configuration for a server."
"""

helps["mysql server create"] = """
type: command
short-summary: Create a server.
examples:
-   name: Create a MySQL server with only required paramaters in North Europe.
    text: az mysql server create -l northeurope -g testgroup -n testsvr -u username
        -p password
-   name: Create a MySQL server with a Standard performance tier and 2 vcore in North
        Europe.
    text: az mysql server create -l northeurope -g testgroup -n testsvr -u username
        -p password \\ --sku-name GP_Gen4_2
-   name: Create a MySQL server with all paramaters set.
    text: az mysql server create -l northeurope -g testgroup -n testsvr -u username
        -p password \\ --sku-name B_Gen4_2 --ssl-enforcement Disabled \\ --storage-size
        51200 --tags "key=value" --version {server-version}
-   name: Create a server.
    text: az mysql server create --sku-name GP_Gen4_2 --version {server-version} --location
        northeurope --name testsvr --admin-user username --resource-group testgroup
        --admin-password password
    crafted: 'True'
"""

helps["mysql server delete"] = """
type: command
short-summary: Delete a server.
"""

helps["mysql server firewall-rule"] = """
type: group
short-summary: Manage firewall rules for a server.
"""

helps["mysql server firewall-rule create"] = """
type: command
short-summary: Create a new firewall rule for a server.
examples:
-   name: Create a firewall rule allowing all connections from all IP addresses.
    text: az mysql server firewall-rule create -g testgroup -s testsvr -n allowall
        --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255
-   name: Create a new firewall rule for a server.
    text: az mysql server firewall-rule create --start-ip-address 0.0.0.0 --server-name
        testsvr --end-ip-address 255.255.255.255 --name allowall --resource-group
        testgroup
    crafted: 'True'
"""

helps["mysql server firewall-rule delete"] = """
type: command
short-summary: Delete a firewall rule.
"""

helps["mysql server firewall-rule list"] = """
type: command
short-summary: List all firewall rules for a server.
"""

helps["mysql server firewall-rule show"] = """
type: command
short-summary: Get the details of a firewall rule.
"""

helps["mysql server firewall-rule update"] = """
type: command
short-summary: Update a firewall rule.
examples:
-   name: Update a firewall rule's start IP address.
    text: az mysql server firewall-rule update -g testgroup -s testsvr -n allowall
        --start-ip-address 0.0.0.1
-   name: Update a firewall rule's start and end IP address.
    text: az mysql server firewall-rule update -g testgroup -s testsvr -n allowall
        --start-ip-address 0.0.0.1 --end-ip-address 255.255.255.254
"""

helps["mysql server georestore"] = """
type: command
short-summary: Georestore a server from backup.
examples:
-   name: Georestore 'testsvr' as 'testsvrnew' where 'testsvrnew' is in same resource
        group as 'testsvr'.
    text: az mysql server georestore -g testgroup -n testsvrnew --source-server testsvr
        -l westus2
-   name: Georestore 'testsvr2' to 'testsvrnew', where 'testsvrnew' is in the different
        resource group as the original server.
    text: |
        az mysql server georestore -g testgroup -n testsvrnew \\
            -s "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforMySQL/servers/testsvr2"
            -l westus2 --sku-name GP_Gen4_2
"""

helps["mysql server list"] = """
type: command
short-summary: List available servers.
examples:
-   name: List all MySQL servers in a subscription.
    text: az mysql server list
-   name: List all MySQL servers in a resource group.
    text: az mysql server list -g testgroup
"""

helps["mysql server replica"] = """
type: group
short-summary: Manage cloud replication.
"""

helps["mysql server replica create"] = """
type: command
short-summary: Create a cloud replica for a server.
examples:
-   name: Create replica for server testsvr.
    text: az mysql server replica create -n testreplsvr -g testgroup -s testsvr
-   name: Create replica testreplsvr for server testsvr2, where 'testreplsvr' is in
        a different resource group.
    text: |
        az mysql server replica create -n testreplsvr -g testgroup \\
            -s "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforMySQL/servers/testsvr2"
"""

helps["mysql server replica list"] = """
type: command
short-summary: List all replicas for a given server.
"""

helps["mysql server replica stop"] = """
type: command
short-summary: Stop replica to make it an individual server.
examples:
-   name: Stop server testsvr as replica and make it an individual server.
    text: az mysql server replica stop -g testgroup -n testsvr
"""

helps["mysql server restore"] = """
type: command
short-summary: Restore a server from backup.
examples:
-   name: Restore 'testsvr' as 'testsvrnew'.
    text: az mysql server restore -g testgroup -n testsvrnew --source-server testsvr
        --restore-point-in-time "2017-06-15T13:10:00Z"
-   name: Restore 'testsvr2' to 'testsvrnew', where 'testsvrnew' is in a different
        resource group than the backup.
    text: |
        az mysql server restore -g testgroup -n testsvrnew \\
            -s "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforMySQL/servers/testsvr2" \\
            --restore-point-in-time "2017-06-15T13:10:00Z"
"""

helps["mysql server show"] = """
type: command
short-summary: Get the details of a server.
"""

helps["mysql server update"] = """
type: command
short-summary: Update a server.
examples:
-   name: Update a server's sku.
    text: az mysql server update -g testgroup -n testsvrnew --sku-name GP_Gen5_4
-   name: Update a server's tags.
    text: az mysql server update -g testgroup -n testsvrnew --tags "k1=v1" "k2=v2"
"""

helps["mysql server vnet-rule"] = """
type: group
short-summary: Manage a server's virtual network rules.
"""

helps["mysql server vnet-rule create"] = """
type: command
short-summary: Create a virtual network rule to allows access to a MySQL server.
examples:
-   name: Create a virtual network rule by providing the subnet id.
    text: az mysql server vnet-rule create -g testgroup -s testsvr -n vnetRuleName
        --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/vnetName/subnets/subnetName
-   name: Create a vnet rule by providing the vnet and subnet name. The subnet id
        is created by taking the resource group name and subscription id of the server.
    text: az mysql server vnet-rule create -g testgroup -s testsvr -n vnetRuleName
        --subnet subnetName --vnet-name vnetName
-   name: Create a virtual network rule to allows access to a MySQL server.
    text: az mysql server vnet-rule create --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/vnetName/subnets/subnetName
        --server-name testsvr --name vnetRuleName --resource-group testgroup
    crafted: 'True'
"""

helps["mysql server vnet-rule update"] = """
type: command
short-summary: Update a virtual network rule.
"""

helps["mysql server wait"] = """
type: command
short-summary: Wait for server to satisfy certain conditions.
"""

helps["mysql server-logs"] = """
type: group
short-summary: Manage server logs.
"""

helps["mysql server-logs download"] = """
type: command
short-summary: Download log files.
examples:
-   name: Download log files f1 and f2 to the current directory from the server 'testsvr'.
    text: az mysql server-logs download -g testgroup -s testsvr -n f1.log f2.log
"""

helps["mysql server-logs list"] = """
type: command
short-summary: List log files for a server.
examples:
-   name: List log files for 'testsvr' modified in the last 72 hours (default value).
    text: az mysql server-logs list -g testgroup -s testsvr
-   name: List log files for 'testsvr' modified in the last 10 hours.
    text: az mysql server-logs list -g testgroup -s testsvr --file-last-written 10
-   name: List log files for 'testsvr' less than 30Kb in size.
    text: az mysql server-logs list -g testgroup -s testsvr --max-file-size 30
"""

helps["postgres"] = """
type: group
short-summary: Manage Azure Database for PostgreSQL servers.
"""

helps["postgres db"] = """
type: group
short-summary: Manage PostgreSQL databases on a server.
"""

helps["postgres db create"] = """
type: command
short-summary: Create a PostgreSQL database.
examples:
-   name: Create database 'testdb' in the server 'testsvr' with the default parameters.
    text: az postgres db create -g testgroup -s testsvr -n testdb --admin-user myadmin
        --admin-password {server_admin_password} --sku-name GP_Gen4_2 --version 5.7
-   name: Create database 'testdb' in server 'testsvr' with a given character set
        and collation rules.
    text: az postgres db create -g testgroup -s testsvr -n testdb --charset {valid_charset}
        --collation {valid_collation} --admin-user myadmin --admin-password {server_admin_password}
        --sku-name GP_Gen4_2 --version 5.7
"""

helps["postgres db delete"] = """
type: command
short-summary: Delete a database.
examples:
-   name: Delete database 'testdb' in the server 'testsvr'.
    text: az postgres db delete -g testgroup -s testsvr -n testdb
"""

helps["postgres db list"] = """
type: command
short-summary: List the databases for a server.
examples:
-   name: List databases in the server 'testsvr'.
    text: az postgres db list -g testgroup -s testsvr
"""

helps["postgres db show"] = """
type: command
short-summary: Show the details of a database.
examples:
-   name: Show database 'testdb' in the server 'testsvr'.
    text: az postgres db show -g testgroup -s testsvr -n testdb
"""

helps["postgres server"] = """
type: group
short-summary: Manage PostgreSQL servers.
"""

helps["postgres server configuration"] = """
type: group
short-summary: Manage configuration values for a server.
"""

helps["postgres server configuration list"] = """
type: command
short-summary: List the configuration values for a server.
"""

helps["postgres server configuration set"] = """
type: command
short-summary: Update the configuration of a server.
examples:
-   name: Set a new configuration value.
    text: az postgres server configuration set -g testgroup -s testsvr -n {config_name}
        --value {config_value}
-   name: Set a configuration value to its default.
    text: az postgres server configuration set -g testgroup -s testsvr -n {config_name}
"""

helps["postgres server configuration show"] = """
type: command
short-summary: Get the configuration for a server."
"""

helps["postgres server create"] = """
type: command
short-summary: Create a server.
examples:
-   name: Create a PostgreSQL server with only required paramaters in North Europe.
    text: az postgres server create -l northeurope -g testgroup -n testsvr -u username
        -p password
-   name: Create a PostgreSQL server with a Standard performance tier and 2 vcore
        in North Europe.
    text: az postgres server create -l northeurope -g testgroup -n testsvr -u username
        -p password \\ --sku-name GP_Gen4_2
-   name: Create a PostgreSQL server with all paramaters set.
    text: az postgres server create -l northeurope -g testgroup -n testsvr -u username
        -p password \\ --sku-name B_Gen4_2 --ssl-enforcement Disabled \\ --storage-size
        51200 --tags "key=value" --version {server-version}
-   name: Create a server.
    text: az postgres server create --sku-name GP_Gen4_2 --version {server-version}
        --storage-size 51200 --location northeurope --name testsvr --admin-user username
        --resource-group testgroup --admin-password password
    crafted: 'True'
"""

helps["postgres server delete"] = """
type: command
short-summary: Delete a server.
"""

helps["postgres server firewall-rule"] = """
type: group
short-summary: Manage firewall rules for a server.
"""

helps["postgres server firewall-rule create"] = """
type: command
short-summary: Create a new firewall rule for a server.
examples:
-   name: Create a firewall rule allowing all connections from all IP addresses.
    text: az postgres server firewall-rule create -g testgroup -s testsvr -n allowall
        --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255
-   name: Create a new firewall rule for a server.
    text: az postgres server firewall-rule create --start-ip-address 0.0.0.0 --server-name
        testsvr --end-ip-address 255.255.255.255 --name allowall --resource-group
        testgroup
    crafted: 'True'
"""

helps["postgres server firewall-rule delete"] = """
type: command
short-summary: Delete a firewall rule.
examples:
-   name: Delete a firewall rule.
    text: az postgres server firewall-rule delete --server-name MyServer --yes  --name
        MyFirewallRule --resource-group MyResourceGroup
    crafted: 'True'
"""

helps["postgres server firewall-rule list"] = """
type: command
short-summary: List all firewall rules for a server.
examples:
-   name: List all firewall rules for a server.
    text: az postgres server firewall-rule list --server-name MyServer --resource-group
        MyResourceGroup
    crafted: 'True'
"""

helps["postgres server firewall-rule show"] = """
type: command
short-summary: Get the details of a firewall rule.
"""

helps["postgres server firewall-rule update"] = """
type: command
short-summary: Update a firewall rule.
examples:
-   name: Update a firewall rule's start IP address.
    text: az postgres server firewall-rule update -g testgroup -s testsvr -n allowall
        --start-ip-address 0.0.0.1
-   name: Update a firewall rule's start and end IP address.
    text: az postgres server firewall-rule update -g testgroup -s testsvr -n allowall
        --start-ip-address 0.0.0.1 --end-ip-address 255.255.255.254
"""

helps["postgres server georestore"] = """
type: command
short-summary: Georestore a server from backup.
examples:
-   name: Georestore 'testsvr' as 'testsvrnew' where 'testsvrnew' is in same resource
        group as 'testsvr'.
    text: az postgres server georestore -g testgroup -n testsvrnew --source-server
        testsvr -l westus2
-   name: Georestore 'testsvr2' to 'testsvrnew', where 'testsvrnew' is in the different
        resource group as the original server.
    text: |
        az postgres server georestore -g testgroup -n testsvrnew \\
            -s "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforPostgreSQL/servers/testsvr2"
            -l westus2 --sku-name GP_Gen4_2
"""

helps["postgres server list"] = """
type: command
short-summary: List available servers.
examples:
-   name: List all PostgreSQL servers in a subscription.
    text: az postgres server list
-   name: List all PostgreSQL servers in a resource group.
    text: az postgres server list -g testgroup
-   name: List available servers.
    text: az postgres server list --resource-group testgroup
    crafted: 'True'
"""

helps["postgres server restore"] = """
type: command
short-summary: Restore a server from backup.
examples:
-   name: Restore 'testsvr' as 'testsvrnew'.
    text: az postgres server restore -g testgroup -n testsvrnew --source-server testsvr
        --restore-point-in-time "2017-06-15T13:10:00Z"
-   name: Restore 'testsvr2' to 'testsvrnew', where 'testsvrnew' is in a different
        resource group than the backup.
    text: |
        az postgres server restore -g testgroup -n testsvrnew \\
            -s "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforPostgreSQL/servers/testsvr2" \\
            --restore-point-in-time "2017-06-15T13:10:00Z"
"""

helps["postgres server show"] = """
type: command
short-summary: Get the details of a server.
examples:
-   name: Get the details of a server.
    text: az postgres server show --name MyServer --resource-group MyResourceGroup
    crafted: 'True'
"""

helps["postgres server update"] = """
type: command
short-summary: Update a server.
examples:
-   name: Update a server's sku.
    text: az postgres server update -g testgroup -n testsvrnew --sku-name GP_Gen5_4
-   name: Update a server's tags.
    text: az postgres server update -g testgroup -n testsvrnew --tags "k1=v1" "k2=v2"
"""

helps["postgres server vnet-rule"] = """
type: group
short-summary: Manage a server's virtual network rules.
examples:
-   name: Gets a list of virtual network rules in a server.
    text: az postgres server vnet-rule list --server-name MyServer --resource-group
        MyResourceGroup
    crafted: 'True'
-   name: Deletes the virtual network rule with the given name.
    text: az postgres server vnet-rule delete --resource-group MyResourceGroup --server-name
        MyServer --name MyVnetRule
    crafted: 'True'
"""

helps["postgres server vnet-rule create"] = """
type: command
short-summary: Create a virtual network rule to allows access to a PostgreSQL server.
examples:
-   name: Create a virtual network rule by providing the subnet id.
    text: az postgres server vnet-rule create -g testgroup -s testsvr -n vnetRuleName
        --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/vnetName/subnets/subnetName
-   name: Create a vnet rule by providing the vnet and subnet name. The subnet id
        is created by taking the resource group name and subscription id of the server.
    text: az postgres server vnet-rule create -g testgroup -s testsvr -n vnetRuleName
        --subnet subnetName --vnet-name vnetName
-   name: Create a virtual network rule to allows access to a PostgreSQL server.
    text: az postgres server vnet-rule create --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/vnetName/subnets/subnetName
        --ignore-missing-endpoint {ignore-missing-endpoint} --resource-group testgroup
        --server-name testsvr --name vnetRuleName
    crafted: 'True'
"""

helps["postgres server vnet-rule update"] = """
type: command
short-summary: Update a virtual network rule.
"""

helps["postgres server wait"] = """
type: command
short-summary: Wait for server to satisfy certain conditions.
"""

helps["postgres server-logs"] = """
type: group
short-summary: Manage server logs.
"""

helps["postgres server-logs download"] = """
type: command
short-summary: Download log files.
examples:
-   name: Download log files f1 and f2 to the current directory from the server 'testsvr'.
    text: az postgres server-logs download -g testgroup -s testsvr -n f1.log f2.log
-   name: Download log files.
    text: az postgres server-logs download --server-name testsvr --name f1.log f2.log
        --resource-group testgroup
    crafted: 'True'
"""

helps["postgres server-logs list"] = """
type: command
short-summary: List log files for a server.
examples:
-   name: List log files for 'testsvr' modified in the last 72 hours (default value).
    text: az postgres server-logs list -g testgroup -s testsvr
-   name: List log files for 'testsvr' modified in the last 10 hours.
    text: az postgres server-logs list -g testgroup -s testsvr --file-last-written
        10
-   name: List log files for 'testsvr' less than 30Kb in size.
    text: az postgres server-logs list -g testgroup -s testsvr --max-file-size 30
-   name: List log files for a server.
    text: az postgres server-logs list --output json --query [0] --server-name testsvr
        --resource-group testgroup
    crafted: 'True'
"""

