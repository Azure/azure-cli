# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['sql'] = """
    type: group
    short-summary: Manage Azure SQL Databases and Data Warehouses.
    """
helps['sql db'] = """
    type: group
    short-summary: Manage databases.
    """
helps['sql db copy'] = """
    type: command
    short-summary: Creates a copy of an existing database.
    """
helps['sql db create'] = """
    type: command
    short-summary: Creates a database.
    """
helps['sql db delete'] = """
    type: command
    short-summary: Deletes a database or data warehouse.
    """
helps['sql db list'] = """
    type: command
    short-summary: Lists all databases and data warehouses in a server, or all databases in an elastic pool.
    """
helps['sql db list-editions'] = """
    type: command
    short-summary: Shows database editions that are available for your subscription.
    long-summary: Also includes available service objectives and storage limits. In order to reduce
                  verbosity, settings to intentionally reduce storage limits are hidden by default.
    examples:
        - name: Show all database editions in a location.
          text: az sql db list-editions -l westus
        - name: Show all available database service objectives for Standard edition.
          text: az sql db list-editions -l westus --edition Standard
        - name: Show available max database sizes for P1 service objective
          text: az sql db list-editions -l westus --service-objective P1 --show-details max-size
    """
helps['sql db show'] = """
    type: command
    short-summary: Gets a database or data warehouse.
    """
helps['sql db update'] = """
    type: command
    short-summary: Updates a database.
    """
helps['sql db audit-policy'] = """
    type: group
    short-summary: Manage a database's auditing policy.
    """
helps['sql db audit-policy update'] = """
    type: command
    short-summary: Updates a database's auditing policy.
    long-summary: If the policy is being enabled, storage_account or both storage_endpoint and
                  storage_account_access_key must be specified.
    examples:
        - name: Enable by specifying storage account name
          text: az sql db audit-policy update -g mygroup -s myserver -n mydb
                --state Enabled --storage-account mystorage
        - name: Enable by specifying storage endpoint and key
          text: az sql db audit-policy update -g mygroup -s myserver -n mydb
                --state Enabled --storage-endpoint https://mystorage.blob.core.windows.net
                --storage-key MYKEY==
        - name: Set the list of audit actions
          text: az sql db audit-policy update -g mygroup -s myserver -n mydb
                --actions FAILED_DATABASE_AUTHENTICATION_GROUP 'UPDATE on database::mydb by public'
        - name: Add an audit action
          text: az sql db audit-policy update -g mygroup -s myserver -n mydb
                --add auditActionsAndGroups FAILED_DATABASE_AUTHENTICATION_GROUP
        - name: Remove an audit action by list index
          text: az sql db audit-policy update -g mygroup -s myserver -n mydb
                --remove auditActionsAndGroups 0
        - name: Disable an auditing policy
          text: az sql db audit-policy update -g mygroup -s myserver -n mydb
                --state Disabled
    """
helps['sql db replica'] = """
    type: group
    short-summary: Manage replication between databases.
    """
helps['sql db replica create'] = """
    type: command
    short-summary: Creates a database as a readable secondary replica of an existing database.
    """
helps['sql db replica set-primary'] = """
    type: command
    short-summary: Sets which replica database is primary by failing over from the current primary replica database.
    """
helps['sql db replica list-links'] = """
    type: command
    short-summary: Lists the replicas of a database and corresponding replication status.
    """
helps['sql db replica delete-link'] = """
    type: command
    short-summary: Permanently stops data replication between two database replicas.
    """
helps['sql db export'] = """
    type: command
    short-summary: Exports a database to a bacpac.
    examples:
        - name: Get SAS key for use in export operation
          text: az storage blob generate-sas --account-name myAccountName -c myContainer -n myBacpac.bacpac --permissions w --expiry 2018-01-01T00:00:00Z
        - name: Export bacpac using SAS key
          text: az sql db export -s myserver -n mydatabase -g mygroup -p password -u login --storage-key "?sr=b&sp=rw&se=2018-01-01T00%3A00%3A00Z&sig=mysignature&sv=2015-07-08" --storage-key-type SharedAccessKey --storage-uri https://mystorageaccount.blob.core.windows.net/bacpacs/mybacpac.bacpac
        - name: Export bacpac using storage account Key
          text: az sql db export -s myserver -n mydatabase -g mygroup -p password -u login --storage-key MYKEY== --storage-key-type StorageAccessKey --storage-uri https://mystorageaccount.blob.core.windows.net/bacpacs/mybacpac.bacpac
    """
helps['sql db import'] = """
    type: command
    short-summary: Imports a bacpac into an existing database.
    examples:
        - name: Get SAS key for use in import operation
          text: az storage blob generate-sas --account-name myAccountName -c myContainer -n myBacpac.bacpac --permissions r --expiry 2018-01-01T00:00:00Z
        - name: Import bacpac into an existing database using SAS key
          text: az sql db import -s myserver -n mydatabase -g mygroup -p password -u login --storage-key "?sr=b&sp=rw&se=2018-01-01T00%3A00%3A00Z&sig=mysignature&sv=2015-07-08" --storage-key-type SharedAccessKey --storage-uri https://mystorageaccount.blob.core.windows.net/bacpacs/mybacpac.bacpac
        - name: Import bacpac into an existing database using storage account key
          text: az sql db import -s myserver -n mydatabase -g mygroup -p password -u login --storage-key MYKEY== --storage-key-type StorageAccessKey --storage-uri https://mystorageaccount.blob.core.windows.net/bacpacs/mybacpac.bacpac
    """
helps['sql db restore'] = """
    type: command
    short-summary: Creates a new database by restoring from a database backup.
    """
helps['sql db threat-policy'] = """
    type: group
    short-summary: Manage a database's threat detection policy.
    """
helps['sql db threat-policy update'] = """
    type: command
    short-summary: Updates a database's threat detection policy.
    long-summary: If the policy is being enabled, storage_account or both storage_endpoint and
                  storage_account_access_key must be specified.
    examples:
        - name: Enable by specifying storage account name
          text: az sql db threat-policy update -g mygroup -s myserver -n mydb
                --state Enabled --storage-account mystorage
        - name: Enable by specifying storage endpoint and key
          text: az sql db threat-policy update -g mygroup -s myserver -n mydb
                --state Enabled --storage-endpoint https://mystorage.blob.core.windows.net
                --storage-key MYKEY==
        - name: Disable a subset of alert types
          text: az sql db threat-policy update -g mygroup -s myserver -n mydb
                --disabled-alerts Sql_Injection_Vulnerability Access_Anomaly
        - name: Configure email recipients
          text: az sql db threat-policy update -g mygroup -s myserver -n mydb
                --email-addresses me@examlee.com you@example.com --email-account-admins
                Enabled
        - name: Disable
          text: az sql db threat-policy update -g mygroup -s myserver -n mydb
                --state Disabled
    """
# helps['sql db restore-point'] = """
#             type: group
#             short-summary: Manage database restore points.
#             """
# helps['sql db transparent-data-encryption'] = """
#             type: group
#             short-summary: Manage database transparent data encryption.
#             """
# helps['sql db service-tier-advisor'] = """
#             type: group
#             short-summary: Manage database service tier advisors.
#             """
helps['sql dw'] = """
    type: group
    short-summary: Manage data warehouses.
    """
helps['sql dw create'] = """
    type: command
    short-summary: Creates a data warehouse.
    """
helps['sql dw delete'] = """
    type: command
    short-summary: Deletes a database or data warehouse.
    """
helps['sql dw list'] = """
    type: command
    short-summary: Lists all data warehouses in a server.
    """
helps['sql dw show'] = """
    type: command
    short-summary: Gets a database or data warehouse.
    """
helps['sql dw update'] = """
    type: command
    short-summary: Updates a data warehouse.
    """
helps['sql elastic-pool'] = """
    type: group
    short-summary: Manage elastic pools. An elastic pool is an allocation of CPU, IO, and memory resources. Databases inside the pool share these resources.
    """
helps['sql elastic-pool create'] = """
    type: command
    short-summary: Creates an elastic pool.
    """
helps['sql elastic-pool list-editions'] = """
    type: command
    short-summary: Shows elastic pool editions that are available for your subscription.
    long-summary: Also includes available pool DTU settings, storage limits, and per database
                  settings. In order to reduce verbosity, additional storage limits and per
                  database settings are hidden by default.
    examples:
        - name: Show all elastic pool editions and pool DTU limits in a location.
          text: az sql elastic-pool list-editions -l westus
        - name: Show all pool DTU limits for Standard edition.
          text: az sql elastic-pool list-editions -l westus --edition Standard
        - name: Show available max sizes for elastic pools with 100 DTUs
          text: az sql elastic-pool list-editions -l westus --dtu 100 --show-details max-size
        - name: Show available per database settings for Standard 100 DTU elastic pools
          text: az sql elastic-pool list-editions -l westus --edition Standard --dtu 100
                --show-details db-min-dtu db-max-dtu db-max-size
    """
helps['sql elastic-pool update'] = """
    type: command
    short-summary: Updates an elastic pool.
    """
# helps['sql elastic-pool recommended'] = """
#             type: group
#             short-summary: Manages recommended elastic pools.
#             """
# helps['sql elastic-pool recommended db'] = """
#             type: group
#             short-summary: Manage recommended elastic pool databases.
#             """
helps['sql server'] = """
    type: group
    short-summary: Manage servers. Servers contain databases, data warehouses, and elastic pools.
    """
helps['sql server create'] = """
    type: command
    short-summary: Creates a server.
    """
helps['sql server list'] = """
    type: command
    short-summary: Lists servers.
    """
helps['sql server update'] = """
    type: command
    short-summary: Updates a server.
    """
helps['sql server firewall-rule'] = """
    type: group
    short-summary: Manage a server's firewall rules.
    """
# helps['sql server firewall-rule allow-all-azure-ips'] = """
#             type: command
#             short-summary: Create a firewall rule that allows all Azure IP addresses to access the server.
#             """
helps['sql server firewall-rule create'] = """
    type: command
    short-summary: Creates a firewall rule.
    """
helps['sql server firewall-rule update'] = """
    type: command
    short-summary: Updates a firewall rule.
    """
helps['sql server firewall-rule show'] = """
    type: command
    short-summary: Shows the detail of a firewall rule.
    """
helps['sql server firewall-rule list'] = """
    type: command
    short-summary: Lists the firewall rules.
    """
