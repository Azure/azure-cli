# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["sql mi list"] = """
"type": |-
    command
"short-summary": |-
    List available managed instances.
"""

helps["sql db replica set-primary"] = """
"type": |-
    command
"short-summary": |-
    Set the primary replica database by failing over from the current primary replica database.
"""

helps["sql db audit-policy"] = """
"type": |-
    group
"short-summary": |-
    Manage a database's auditing policy.
"""

helps["sql dw delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a data warehouse.
"""

helps["sql server firewall-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a firewall rule.
"""

helps["sql server key delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes a server key.
"""

helps["sql db audit-policy update"] = """
"type": |-
    command
"short-summary": |-
    Update a database's auditing policy.
"long-summary": |-
    If the policy is being enabled, `--storage-account` or both `--storage-endpoint` and `--storage-key` must be specified.
"""

helps["sql server conn-policy show"] = """
"type": |-
    command
"short-summary": |-
    Gets a server's secure connection policy.
"""

helps["sql db op"] = """
"type": |-
    group
"short-summary": |-
    Manage operations on a database.
"""

helps["sql dw create"] = """
"type": |-
    command
"short-summary": |-
    Create a data warehouse.
"""

helps["sql db create"] = """
"type": |-
    command
"short-summary": |-
    Create a database.
"long-summary": |-
    A full list of performance level options can be seen by executing `az sql db list-editions -a -o table -l LOCATION`.
"examples":
-   "name": |-
        Create a database.
    "text": |-
        az sql db create --server myserver --name mydb --collation <collation> --elastic-pool <elastic-pool> --resource-group mygroup
"""

helps["sql dw"] = """
"type": |-
    group
"short-summary": |-
    Manage data warehouses.
"""

helps["sql server vnet-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a virtual network rule.
"""

helps["sql failover-group"] = """
"type": |-
    group
"short-summary": |-
    Manage SQL Failover Groups.
"""

helps["sql db rename"] = """
"type": |-
    command
"short-summary": |-
    Rename a database.
"""

helps["sql db import"] = """
"type": |-
    command
"short-summary": |-
    Imports a bacpac into an existing database.
"""

helps["sql db tde set"] = """
"type": |-
    command
"short-summary": |-
    Sets a database's transparent data encryption configuration.
"""

helps["sql server conn-policy update"] = """
"type": |-
    command
"short-summary": |-
    Updates a server's secure connection policy.
"""

helps["sql server update"] = """
"type": |-
    command
"short-summary": |-
    Update a server.
"""

helps["sql server"] = """
"type": |-
    group
"short-summary": |-
    Manage SQL servers.
"""

helps["sql elastic-pool create"] = """
"type": |-
    command
"short-summary": |-
    Create an elastic pool.
"""

helps["sql db threat-policy"] = """
"type": |-
    group
"short-summary": |-
    Manage a database's threat detection policies.
"""

helps["sql db update"] = """
"type": |-
    command
"short-summary": |-
    Update a database.
"""

helps["sql db show"] = """
"type": |-
    command
"short-summary": |-
    Get the details for a database.
"examples":
-   "name": |-
        Get the details for a database.
    "text": |-
        az sql db show --server <server> --name MyAzureSQLDatabase --resource-group MyResourceGroup
"""

helps["sql midb show"] = """
"type": |-
    command
"short-summary": |-
    Get the details for a managed database.
"""

helps["sql server tde-key"] = """
"type": |-
    group
"short-summary": |-
    Manage a server's encryption protector.
"""

helps["sql server dns-alias set"] = """
"type": |-
    command
"short-summary": |-
    Sets a server to which DNS alias should point
"""

helps["sql dw show"] = """
"type": |-
    command
"short-summary": |-
    Get the details for a data warehouse.
"""

helps["sql db replica create"] = """
"type": |-
    command
"short-summary": |-
    Create a database as a readable secondary replica of an existing database.
"long-summary": |-
    A full list of performance level options can be seen by executing `az sql db list-editions -a -o table -l LOCATION`. The secondary database must have the same edition as the primary database.
"""

helps["sql"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure SQL Databases and Data Warehouses.
"""

helps["sql server vnet-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create a virtual network rule to allows access to an Azure SQL server.
"""

helps["sql server firewall-rule show"] = """
"type": |-
    command
"short-summary": |-
    Shows the details for a firewall rule.
"""

helps["sql db copy"] = """
"type": |-
    command
"short-summary": |-
    Create a copy of a database.
"long-summary": |-
    A full list of performance level options can be seen by executing `az sql db list-editions -a -o table -l LOCATION`. The copy destination database must have the same edition as the source database, but you can change the edition after the copy has completed.
"""

helps["sql server tde-key set"] = """
"type": |-
    command
"short-summary": |-
    Sets the server's encryption protector.
"""

helps["sql db replica"] = """
"type": |-
    group
"short-summary": |-
    Manage replication between databases.
"""

helps["sql mi update"] = """
"type": |-
    command
"short-summary": |-
    Update a managed instance.
"examples":
-   "name": |-
        Update a managed instance.
    "text": |-
        az sql mi update --capacity vcorecapacity --name myinstance --resource-group mygroup
"""

helps["sql db replica delete-link"] = """
"type": |-
    command
"short-summary": |-
    Permanently stop data replication between two database replicas.
"""

helps["sql failover-group set-primary"] = """
"type": |-
    command
"short-summary": |-
    Set the primary of the failover group by failing over all databases from the current primary server.
"""

helps["sql db threat-policy update"] = """
"type": |-
    command
"short-summary": |-
    Update a database's threat detection policy.
"long-summary": |-
    If the policy is being enabled, storage_account or both storage_endpoint and storage_account_access_key must be specified.
"""

helps["sql elastic-pool list-editions"] = """
"type": |-
    command
"short-summary": |-
    List elastic pool editions available for the active subscription.
"long-summary": |-
    Also includes available pool DTU settings, storage limits, and per database settings. In order to reduce verbosity, additional storage limits and per database settings are hidden by default.
"""

helps["sql server create"] = """
"type": |-
    command
"short-summary": |-
    Create a server.
"examples":
-   "name": |-
        Create a server.
    "text": |-
        az sql server create --admin-password myadminpassword --admin-user myadminuser --resource-group mygroup --location westus --name myserver
"""

helps["sql failover-group create"] = """
"type": |-
    command
"short-summary": |-
    Creates a failover group.
"""

helps["sql db show-connection-string"] = """
"type": |-
    command
"short-summary": |-
    Generates a connection string to a database.
"""

helps["sql elastic-pool update"] = """
"type": |-
    command
"short-summary": |-
    Update an elastic pool.
"""

helps["sql db list-editions"] = """
"type": |-
    command
"short-summary": |-
    Show database editions available for the currently active subscription.
"long-summary": |-
    Includes available service objectives and storage limits. In order to reduce verbosity, settings to intentionally reduce storage limits are hidden by default.
"""

helps["sql mi delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a managed instance.
"""

helps["sql server firewall-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage a server's firewall rules.
"""

helps["sql server key show"] = """
"type": |-
    command
"short-summary": |-
    Shows a server key.
"""

helps["sql server list"] = """
"type": |-
    command
"short-summary": |-
    List available servers.
"examples":
-   "name": |-
        List available servers.
    "text": |-
        az sql server list --output json --query [0] --resource-group mygroup
"""

helps["sql midb restore"] = """
"type": |-
    command
"short-summary": |-
    Restore a managed database.
"""

helps["sql elastic-pool op cancel"] = """
"type": |-
    command
"""

helps["sql server vnet-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage a server's virtual network rules.
"""

helps["sql failover-group update"] = """
"type": |-
    command
"short-summary": |-
    Updates the failover group.
"""

helps["sql midb list"] = """
"type": |-
    command
"short-summary": |-
    List maanged databases on a managed instance.
"""

helps["sql mi create"] = """
"type": |-
    command
"short-summary": |-
    Create a managed instance.
"""

helps["sql dw update"] = """
"type": |-
    command
"short-summary": |-
    Update a data warehouse.
"""

helps["sql db"] = """
"type": |-
    group
"short-summary": |-
    Manage databases.
"""

helps["sql db export"] = """
"type": |-
    command
"short-summary": |-
    Export a database to a bacpac.
"examples":
-   "name": |-
        Export a database to a bacpac.
    "text": |-
        az sql db export --storage-key-type SharedAccessKey --server <server> --storage-uri <storage-uri> --resource-group MyResourceGroup --admin-user <admin-user> --name MyAzureSQLDatabase --storage-key <storage-key> --admin-password <admin-password>
"""

helps["sql server key create"] = """
"type": |-
    command
"short-summary": |-
    Creates a server key.
"""

helps["sql server key"] = """
"type": |-
    group
"short-summary": |-
    Manage a server's keys.
"""

helps["sql db list"] = """
"type": |-
    command
"short-summary": |-
    List databases a server or elastic pool.
"examples":
-   "name": |-
        List databases a server or elastic pool.
    "text": |-
        az sql db list --output json --server <server> --query [0] --resource-group MyResourceGroup
-   "name": |-
        Returns database usages.
    "text": |-
        az sql db list-usages --server <server> --resource-group MyResourceGroup --name MyAzureSQLDatabase
"""

helps["sql midb create"] = """
"type": |-
    command
"short-summary": |-
    Create a managed database.
"""

helps["sql dw list"] = """
"type": |-
    command
"short-summary": |-
    List data warehouses for a server.
"""

helps["sql server ad-admin update"] = """
"type": |-
    command
"short-summary": |-
    Update an existing server Active Directory administrator.
"""

helps["sql server ad-admin"] = """
"type": |-
    group
"short-summary": |-
    Manage a server's Active Directory administrator.
"""

helps["sql server firewall-rule list"] = """
"type": |-
    command
"short-summary": |-
    List a server's firewall rules.
"""

helps["sql server dns-alias"] = """
"type": |-
    group
"short-summary": |-
    Manage a server's DNS aliases.
"""

helps["sql elastic-pool op"] = """
"type": |-
    group
"short-summary": |-
    Manage operations on an elastic pool.
"""

helps["sql mi show"] = """
"type": |-
    command
"short-summary": |-
    Get the details for a managed instance.
"examples":
-   "name": |-
        Get the details for a managed instance.
    "text": |-
        az sql mi show --name myinstance --resource-group mygroup
"""

helps["sql mi"] = """
"type": |-
    group
"short-summary": |-
    Manage SQL managed instances.
"""

helps["sql server ad-admin create"] = """
"type": |-
    command
"short-summary": |-
    Create a new server Active Directory administrator.
"""

helps["sql elastic-pool"] = """
"type": |-
    group
"short-summary": |-
    Manage elastic pools.
"""

helps["sql db replica list-links"] = """
"type": |-
    command
"short-summary": |-
    List the replicas of a database and their replication status.
"""

helps["sql db delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a database.
"examples":
-   "name": |-
        Delete a database.
    "text": |-
        az sql db delete --server <server> --resource-group MyResourceGroup --yes  --name MyAzureSQLDatabase
"""

helps["sql midb delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a managed database.
"""

helps["sql server conn-policy"] = """
"type": |-
    group
"short-summary": |-
    Manage a server's connection policy.
"""

helps["sql db restore"] = """
"type": |-
    command
"short-summary": |-
    Create a new database by restoring from a backup.
"""

helps["sql db op cancel"] = """
"type": |-
    command
"""

helps["sql server firewall-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update a firewall rule.
"""

helps["sql db tde"] = """
"type": |-
    group
"short-summary": |-
    Manage a database's transparent data encryption.
"""

helps["sql midb"] = """
"type": |-
    group
"short-summary": |-
    Manage SQL managed instance databases.
"""

