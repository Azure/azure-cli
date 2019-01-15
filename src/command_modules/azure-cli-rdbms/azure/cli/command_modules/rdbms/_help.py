# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["mariadb server-logs download"] = """
"type": |-
    command
"short-summary": |-
    Download log files.
"""

helps["postgres server georestore"] = """
"type": |-
    command
"short-summary": |-
    Georestore a server from backup.
"""

helps["mysql server firewall-rule show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a firewall rule.
"""

helps["postgres db delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a database.
"""

helps["mysql server configuration"] = """
"type": |-
    group
"short-summary": |-
    Manage configuration values for a server.
"""

helps["mysql db delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a database.
"""

helps["mariadb server vnet-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage a server's virtual network rules.
"""

helps["mariadb server firewall-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a new firewall rule for a server.
"""

helps["mysql server firewall-rule list"] = """
"type": |-
    command
"short-summary": |-
    List all firewall rules for a server.
"""

helps["mariadb server create"] = """
"type": |-
    command
"short-summary": |-
    Create a server.
"""

helps["postgres server firewall-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage firewall rules for a server.
"""

helps["postgres server vnet-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a virtual network rule.
"""

helps["mysql server firewall-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage firewall rules for a server.
"""

helps["mysql server replica create"] = """
"type": |-
    command
"short-summary": |-
    Create a cloud replica for a server.
"""

helps["mariadb server firewall-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage firewall rules for a server.
"""

helps["postgres server wait"] = """
"type": |-
    command
"short-summary": |-
    Wait for server to satisfy certain conditions.
"""

helps["mariadb server restore"] = """
"type": |-
    command
"short-summary": |-
    Restore a server from backup.
"""

helps["mariadb db delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a database.
"""

helps["mariadb server wait"] = """
"type": |-
    command
"short-summary": |-
    Wait for server to satisfy certain conditions.
"""

helps["mysql server delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a server.
"""

helps["mariadb server configuration list"] = """
"type": |-
    command
"short-summary": |-
    List the configuration values for a server.
"""

helps["postgres server vnet-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a virtual network rule to allows access to a PostgreSQL server.
"""

helps["mysql server-logs"] = """
"type": |-
    group
"short-summary": |-
    Manage server logs.
"""

helps["mariadb db create"] = """
"type": |-
    command
"short-summary": |-
    Create a MariaDB database.
"""

helps["mariadb server-logs list"] = """
"type": |-
    command
"short-summary": |-
    List log files for a server.
"""

helps["postgres server firewall-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a new firewall rule for a server.
"""

helps["mariadb server vnet-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a virtual network rule.
"""

helps["postgres server configuration set"] = """
"type": |-
    command
"short-summary": |-
    Update the configuration of a server.
"""

helps["mariadb server firewall-rule show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a firewall rule.
"""

helps["mariadb db show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a database.
"""

helps["mysql server-logs download"] = """
"type": |-
    command
"short-summary": |-
    Download log files.
"""

helps["mariadb server list"] = """
"type": |-
    command
"short-summary": |-
    List available servers.
"""

helps["mariadb server firewall-rule list"] = """
"type": |-
    command
"short-summary": |-
    List all firewall rules for a server.
"""

helps["mysql server replica"] = """
"type": |-
    group
"short-summary": |-
    Manage cloud replication.
"""

helps["mysql db create"] = """
"type": |-
    command
"short-summary": |-
    Create a MySQL database.
"""

helps["postgres server delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a server.
"""

helps["postgres server-logs"] = """
"type": |-
    group
"short-summary": |-
    Manage server logs.
"""

helps["postgres server update"] = """
"type": |-
    command
"short-summary": |-
    Update a server.
"""

helps["mysql server wait"] = """
"type": |-
    command
"short-summary": |-
    Wait for server to satisfy certain conditions.
"""

helps["mariadb server-logs"] = """
"type": |-
    group
"short-summary": |-
    Manage server logs.
"""

helps["postgres server configuration show"] = """
"type": |-
    command
"short-summary": |-
    Get the configuration for a server."
"""

helps["mysql server"] = """
"type": |-
    group
"short-summary": |-
    Manage MySQL servers.
"""

helps["postgres server-logs download"] = """
"type": |-
    command
"short-summary": |-
    Download log files.
"""

helps["postgres"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Database for PostgreSQL servers.
"""

helps["postgres server show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a server.
"examples":
-   "name": |-
        Get the details of a server.
    "text": |-
        az postgres server show --name MyServer --resource-group MyResourceGroup
"""

helps["postgres server configuration"] = """
"type": |-
    group
"short-summary": |-
    Manage configuration values for a server.
"""

helps["mysql server show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a server.
"""

helps["postgres server-logs list"] = """
"type": |-
    command
"short-summary": |-
    List log files for a server.
"""

helps["mysql"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Database for MySQL servers.
"""

helps["mysql server vnet-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage a server's virtual network rules.
"""

helps["postgres server firewall-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a firewall rule.
"""

helps["mariadb db list"] = """
"type": |-
    command
"short-summary": |-
    List the databases for a server.
"""

helps["mariadb server configuration show"] = """
"type": |-
    command
"short-summary": |-
    Get the configuration for a server."
"""

helps["postgres server list"] = """
"type": |-
    command
"short-summary": |-
    List available servers.
"examples":
-   "name": |-
        List available servers.
    "text": |-
        az postgres server list --resource-group testgroup
"""

helps["postgres server firewall-rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a firewall rule.
"""

helps["mariadb"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Database for MariaDB servers.
"""

helps["mysql server replica stop"] = """
"type": |-
    command
"short-summary": |-
    Stop replica to make it an individual server.
"""

helps["mysql server firewall-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a new firewall rule for a server.
"""

helps["mariadb server show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a server.
"""

helps["mariadb db"] = """
"type": |-
    group
"short-summary": |-
    Manage MariaDB databases on a server.
"""

helps["mysql server configuration show"] = """
"type": |-
    command
"short-summary": |-
    Get the configuration for a server."
"""

helps["mariadb server georestore"] = """
"type": |-
    command
"short-summary": |-
    Georestore a server from backup.
"""

helps["postgres db list"] = """
"type": |-
    command
"short-summary": |-
    List the databases for a server.
"""

helps["mariadb server delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a server.
"""

helps["mysql server firewall-rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a firewall rule.
"""

helps["mysql server list"] = """
"type": |-
    command
"short-summary": |-
    List available servers.
"""

helps["mysql server configuration list"] = """
"type": |-
    command
"short-summary": |-
    List the configuration values for a server.
"""

helps["postgres server vnet-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage a server's virtual network rules.
"""

helps["mysql server vnet-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a virtual network rule.
"""

helps["mysql server vnet-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a virtual network rule to allows access to a MySQL server.
"""

helps["mariadb server vnet-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a virtual network rule to allows access to a MariaDB server.
"""

helps["postgres server configuration list"] = """
"type": |-
    command
"short-summary": |-
    List the configuration values for a server.
"""

helps["mysql server-logs list"] = """
"type": |-
    command
"short-summary": |-
    List log files for a server.
"""

helps["mysql server update"] = """
"type": |-
    command
"short-summary": |-
    Update a server.
"""

helps["mysql server firewall-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a firewall rule.
"""

helps["postgres server firewall-rule show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a firewall rule.
"""

helps["mariadb server firewall-rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a firewall rule.
"""

helps["postgres db"] = """
"type": |-
    group
"short-summary": |-
    Manage PostgreSQL databases on a server.
"""

helps["mysql server restore"] = """
"type": |-
    command
"short-summary": |-
    Restore a server from backup.
"""

helps["mysql db"] = """
"type": |-
    group
"short-summary": |-
    Manage MySQL databases on a server.
"""

helps["postgres db show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a database.
"""

helps["postgres db create"] = """
"type": |-
    command
"short-summary": |-
    Create a PostgreSQL database.
"""

helps["mysql db list"] = """
"type": |-
    command
"short-summary": |-
    List the databases for a server.
"""

helps["mysql server create"] = """
"type": |-
    command
"short-summary": |-
    Create a server.
"examples":
-   "name": |-
        Create a server.
    "text": |-
        az mysql server create --sku-name GP_Gen4_2 --version {server-version} --location northeurope --name testsvr --admin-user username --resource-group testgroup --admin-password password
"""

helps["mysql server configuration set"] = """
"type": |-
    command
"short-summary": |-
    Update the configuration of a server.
"""

helps["mysql db show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a database.
"""

helps["mariadb server configuration"] = """
"type": |-
    group
"short-summary": |-
    Manage configuration values for a server.
"""

helps["mariadb server configuration set"] = """
"type": |-
    command
"short-summary": |-
    Update the configuration of a server.
"""

helps["mariadb server"] = """
"type": |-
    group
"short-summary": |-
    Manage MariaDB servers.
"""

helps["postgres server create"] = """
"type": |-
    command
"short-summary": |-
    Create a server.
"examples":
-   "name": |-
        Create a server.
    "text": |-
        az postgres server create --sku-name GP_Gen4_2 --version {server-version} --storage-size 51200 --location northeurope --name testsvr --admin-user username --resource-group testgroup --admin-password password
"""

helps["postgres server firewall-rule list"] = """
"type": |-
    command
"short-summary": |-
    List all firewall rules for a server.
"""

helps["mariadb server firewall-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a firewall rule.
"""

helps["mysql server georestore"] = """
"type": |-
    command
"short-summary": |-
    Georestore a server from backup.
"""

helps["postgres server"] = """
"type": |-
    group
"short-summary": |-
    Manage PostgreSQL servers.
"examples":
-   "name": |-
        List log files for a server.
    "text": |-
        az postgres server-logs list --output json --query [0] --server-name testsvr --resource-group testgroup
-   "name": |-
        Download log files.
    "text": |-
        az postgres server-logs download --server-name testsvr --name f1.log f2.log --resource-group testgroup
"""

helps["postgres server restore"] = """
"type": |-
    command
"short-summary": |-
    Restore a server from backup.
"""

helps["mariadb server update"] = """
"type": |-
    command
"short-summary": |-
    Update a server.
"""

helps["mysql server replica list"] = """
"type": |-
    command
"short-summary": |-
    List all replicas for a given server.
"""

