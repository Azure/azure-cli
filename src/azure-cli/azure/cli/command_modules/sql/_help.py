# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['sql'] = """
type: group
short-summary: Manage Azure SQL Databases and Data Warehouses.
"""

helps['sql db'] = """
type: group
short-summary: Manage databases.
"""

helps['sql db audit-policy'] = """
type: group
short-summary: Manage a database's auditing policy.
"""

helps['sql db audit-policy wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the database's audit policy is met.
examples:
  - name: Place the CLI in a waiting state until it determines that database's audit policy exists
    text: az sql db audit-policy wait -g mygroup -s myserver -n mydb --exists
"""

helps['sql db audit-policy update'] = """
type: command
short-summary: Update a database's auditing policy.
long-summary: If the policy is being enabled, `--storage-account` or both `--storage-endpoint` and `--storage-key` must be specified.
examples:
  - name: Enable by storage account name.
    text: |
        az sql db audit-policy update -g mygroup -s myserver -n mydb --state Enabled \\
            --bsts Enabled --storage-account mystorage
  - name: Enable by storage endpoint and key.
    text: |
        az sql db audit-policy update -g mygroup -s myserver -n mydb --state Enabled \\
            --bsts Enabled --storage-endpoint https://mystorage.blob.core.windows.net \\
            --storage-key MYKEY==
  - name: Set the list of audit actions.
    text: |
        az sql db audit-policy update -g mygroup -s myserver -n mydb \\
            --actions FAILED_DATABASE_AUTHENTICATION_GROUP 'UPDATE on database::mydb by public'
  - name: Disable an auditing policy.
    text: az sql db audit-policy update -g mygroup -s myserver -n mydb --state Disabled
  - name: Disable a blob storage auditing policy.
    text: az sql db audit-policy update -g mygroup -s myserver -n mydb --bsts Disabled
  - name: Enable a log analytics auditing policy.
    text: |
        az sql db audit-policy update -g mygroup -s myserver -n mydb --state Enabled \\
            --lats Enabled --lawri myworkspaceresourceid
  - name: Disable a log analytics auditing policy.
    text: |
        az sql db audit-policy update -g mygroup -s myserver -n mydb
            --lats Disabled
  - name: Enable an event hub auditing policy.
    text: |
        az sql db audit-policy update -g mygroup -s myserver -n mydb --state Enabled \\
            --event-hub-target-state Enabled \\
            --event-hub-authorization-rule-id eventhubauthorizationruleid \\
            --event-hub eventhubname
  - name: Enable an event hub auditing policy for default event hub.
    text: |
        az sql db audit-policy update -g mygroup -s myserver -n mydb --state Enabled \\
            --event-hub-target-state Enabled \\
            --event-hub-authorization-rule-id eventhubauthorizationruleid
  - name: Disable an event hub auditing policy.
    text: |
        az sql db audit-policy update -g mygroup -s myserver -n mydb
            --event-hub-target-state Disabled
"""

helps['sql db copy'] = """
type: command
short-summary: Create a copy of a database.
long-summary: A full list of performance level options can be seen by executing `az sql db list-editions -a -o table -l LOCATION`. The copy destination database must have the same edition as the source database, but you can change the edition after the copy has completed.
examples:
  - name: Create a database with performance level S0 as a copy of an existing Standard database.
    text: az sql db copy -g mygroup -s myserver -n originalDb --dest-name newDb --service-objective S0
  - name: Create a database with GeneralPurpose edition, Gen4 hardware, and 1 vcore as a copy of an existing GeneralPurpose database.
    text: az sql db copy -g mygroup -s myserver -n originalDb --dest-name newDb -f Gen4 -c 1
  - name: Create a database with local backup storage redundancy as a copy of an existing database
    text: az sql db copy -g mygroup -s myserver -n originalDb --dest-name newDb --backup-storage-redundancy Local

"""

helps['sql db create'] = """
type: command
short-summary: Create a database.
long-summary: A full list of performance level options can be seen by executing `az sql db list-editions -a -o table -l LOCATION`.
examples:
  - name: Create a Standard S0 database.
    text: az sql db create -g mygroup -s myserver -n mydb --service-objective S0
  - name: Create a database with GeneralPurpose edition, Gen4 hardware and 1 vcore
    text: az sql db create -g mygroup -s myserver -n mydb -e GeneralPurpose -f Gen4 -c 1
  - name: Create a database with zone redundancy enabled
    text: az sql db create -g mygroup -s myserver -n mydb -z
  - name: Create a database with zone redundancy explicitly disabled
    text: az sql db create -g mygroup -s myserver -n mydb -z false
  - name: Create a GeneralPurpose Gen5 2 vcore serverless database with auto pause delay of 120 minutes
    text: az sql db create -g mygroup -s myserver -n mydb -e GeneralPurpose -f Gen5 -c 2 --compute-model Serverless --auto-pause-delay 120
  - name: Create a Hyperscale Gen5 2 vcore database with 2 read replicas
    text: az sql db create -g mygroup -s myserver -n mydb -e Hyperscale -f Gen5 -c 2 --read-replicas 2
  - name: Create a GeneralPurpose database with locally redundant backup storage
    text: az sql db create -g mygroup -s myserver -n mydb -e GeneralPurpose --backup-storage-redundancy Local
"""

helps['sql db delete'] = """
type: command
short-summary: Delete a database.
examples:
  - name: Delete a database. (autogenerated)
    text: az sql db delete --name MyAzureSQLDatabase --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql db export'] = """
type: command
short-summary: Export a database to a bacpac.
examples:
  - name: Get an SAS key for use in export operation.
    text: |
        az storage blob generate-sas --account-name myAccountName -c myContainer -n myBacpac.bacpac \\
            --permissions w --expiry 2018-01-01T00:00:00Z
  - name: Export bacpac using an SAS key.
    text: |
        az sql db export -s myserver -n mydatabase -g mygroup -p password -u login \\
            --storage-key "?sr=b&sp=rw&se=2018-01-01T00%3A00%3A00Z&sig=mysignature&sv=2015-07-08" \\
            --storage-key-type SharedAccessKey \\
            --storage-uri https://myAccountName.blob.core.windows.net/myContainer/myBacpac.bacpac
  - name: Export bacpac using a storage account key.
    text: |
        az sql db export -s myserver -n mydatabase -g mygroup -p password -u login \\
            --storage-key MYKEY== --storage-key-type StorageAccessKey \\
            --storage-uri https://myAccountName.blob.core.windows.net/myContainer/myBacpac.bacpac
"""

helps['sql db import'] = """
type: command
short-summary: Imports a bacpac into an existing database.
examples:
  - name: Get an SAS key for use in import operation.
    text: |
        az storage blob generate-sas --account-name myAccountName -c myContainer -n myBacpac.bacpac \\
            --permissions r --expiry 2018-01-01T00:00:00Z
  - name: Import bacpac into an existing database using an SAS key.
    text: |
        az sql db import -s myserver -n mydatabase -g mygroup -p password -u login \\
            --storage-key "?sr=b&sp=rw&se=2018-01-01T00%3A00%3A00Z&sig=mysignature&sv=2015-07-08" \\
            --storage-key-type SharedAccessKey \\
            --storage-uri https://myAccountName.blob.core.windows.net/myContainer/myBacpac.bacpac
  - name: Import bacpac into an existing database using a storage account key.
    text: |
        az sql db import -s myserver -n mydatabase -g mygroup -p password -u login --storage-key MYKEY== \\
            --storage-key-type StorageAccessKey \\
            --storage-uri https://myAccountName.blob.core.windows.net/myContainer/myBacpac.bacpac
"""

helps['sql db list'] = """
type: command
short-summary: List databases on a server or elastic pool.
examples:
  - name: List databases on a server or elastic pool. (autogenerated)
    text: az sql db list --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql db list-editions'] = """
type: command
short-summary: Show database editions available for the currently active subscription.
long-summary: Includes available service objectives and storage limits. In order to reduce verbosity, settings to intentionally reduce storage limits are hidden by default.
examples:
  - name: Show all database editions in a location.
    text: az sql db list-editions -l westus -o table
  - name: Show all available database service objectives for Standard edition.
    text: az sql db list-editions -l westus --edition Standard -o table
  - name: Show available max database sizes for P1 service objective
    text: az sql db list-editions -l westus --service-objective P1 --show-details max-size
"""

helps['sql db str-policy'] = """
type: group
short-summary: Manage SQL database short term retention policy.
"""

helps['sql db str-policy set'] = """
type: command
short-summary: Update short term retention settings for a live database.
examples:
  - name: Set short term retention for a live database.
    text: az sql db str-policy set -g mygroup -s myserver -n mydb --retention-days retentionindays --diffbackup-hours diffbackuphours
"""

helps['sql db str-policy show'] = """
type: command
short-summary: Show the short term retention policy for a live database.
examples:
  - name: Show short term retention policy for a live database.
    text: az sql db str-policy show -g mygroup -s myserver -n mydb
"""

helps['sql db str-policy wait'] = """
type: command
short-summary: Place the CLI in a waiting state until the policy is set.
"""

helps['sql db ltr-policy'] = """
type: group
short-summary: Manage SQL database long term retention policy.
"""

helps['sql db ltr-policy set'] = """
type: command
short-summary: Update long term retention settings for a database.
examples:
  - name: Set long term retention for a database.
    text: az sql db ltr-policy set -g mygroup -s myserver -n mydb --weekly-retention "P1W" --monthly-retention "P6M" --yearly-retention "P1Y" --week-of-year 26
"""

helps['sql db ltr-policy show'] = """
type: command
short-summary: Show the long term retention policy for a database.
examples:
  - name: Show long term retention policy for a database.
    text: az sql db ltr-policy show -g mygroup -s myserver -n mydb
"""

helps['sql db ltr-backup'] = """
type: group
short-summary: Manage SQL database long term retention backups.
"""

helps['sql db ltr-backup show'] = """
type: command
short-summary: Get a long term retention backup for a database.
examples:
  - name: Show long term retention backup for a database.
    text: az sql db ltr-backup show -l southeastasia -s myserver -d mydb -n "3214b3fb-fba9-43e7-96a3-09e35ffcb336;132292152080000000"
"""

helps['sql db ltr-backup list'] = """
type: command
short-summary: List the long term retention backups for a location, server or database.
examples:
  - name: List long term retention backups for a database.
    text: az sql db ltr-backup list -l southeastasia -s myserver -d mydb
  - name: List long term retention backups for a server (list only the latest LTR backups, which belong to live databases).
    text: az sql db ltr-backup list -l southeastasia -s myserver --database-state Live --only-latest-per-database True
  - name: List long term retention backups for a server (with resource group argument).
    text: az sql db ltr-backup list -l southeastasia -g mygroup -s myserver
  - name: List long term retention backups for a location (list only the latest LTR backups, which belong to live databases).
    text: az sql db ltr-backup list -l southeastasia --database-state Live --only-latest-per-database True
  - name: List long term retention backups for a location (with resource group argument).
    text: az sql db ltr-backup list -l southeastasia -g mygroup
"""

helps['sql db ltr-backup delete'] = """
type: command
short-summary: Delete a long term retention backup.
examples:
  - name: Delete long term retention backup for database.
    text: az sql db ltr-backup delete -l southeastasia -s myserver -d mydb -n "3214b3fb-fba9-43e7-96a3-09e35ffcb336;132292152080000000"
"""

helps['sql db ltr-backup restore'] = """
type: command
short-summary: Restore a long term retention backup to a new database.
examples:
  - name: Restore LTR backup.
    text: |
        az sql db ltr-backup restore \\
        --dest-database targetdb --dest-server myserver --dest-resource-group mygroup \\
        --backup-id "/subscriptions/6caa113c-794c-42f8-ab9d-878d8aa104dc/resourceGroups/mygroup/providers/Microsoft.Sql/locations/southeastasia/longTermRetentionServers/myserver/longTermRetentionDatabases/sourcedb/longTermRetentionBackups/3214b3fb-fba9-43e7-96a3-09e35ffcb336;132292152080000000"
"""

helps['sql db ltr-backup wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the database is met.
"""

helps['sql db op'] = """
type: group
short-summary: Manage operations on a database.
"""

helps['sql db op cancel'] = """
type: command
examples:
  - name: Cancel an operation.
    text: az sql db op cancel -g mygroup -s myserver -d mydb -n d2896mydb-2ba8-4c84-bac1-387c430cce40
"""

helps['sql mi op cancel'] = """
type: command
examples:
  - name: Cancel an operation.
    text: az sql mi op cancel -g mygroup --mi myManagedInstance -n d2896mydb-2ba8-4c84-bac1-387c430cce40
"""

helps['sql db rename'] = """
type: command
short-summary: Rename a database.
examples:
  - name: Rename a database. (autogenerated)
    text: az sql db rename --name MyAzureSQLDatabase --new-name MyNew --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql db replica'] = """
type: group
short-summary: Manage replication between databases.
"""

helps['sql db replica create'] = """
type: command
short-summary: Create a database as a readable secondary replica of an existing database.
long-summary: A full list of performance level options can be seen by executing `az sql db list-editions -a -o table -l LOCATION`. The secondary database must have the same edition as the primary database.
examples:
  - name: Create a database with performance level S0 as a secondary replica of an existing Standard database.
    text: az sql db replica create -g mygroup -s myserver -n originalDb --partner-server newDb --service-objective S0
  - name: Create a database with GeneralPurpose edition, Gen4 hardware, and 1 vcore as a secondary replica of an existing GeneralPurpose database
    text: az sql db replica create -g mygroup -s myserver -n originalDb --partner-server newDb -f Gen4 -c 1
  - name: Create a database with with zone redundant backup storage as a secondary replica of an existing database.
    text: az sql db replica create -g mygroup -s myserver -n originalDb --partner-server newDb --backup-storage-redundancy Zone
"""

helps['sql db replica delete-link'] = """
type: command
short-summary: Permanently stop data replication between two database replicas.
"""

helps['sql db replica list-links'] = """
type: command
short-summary: List the replicas of a database and their replication status.
examples:
  - name: List the replicas of a database and their replication status. (autogenerated)
    text: az sql db replica list-links --name MyAzureSQLDatabase --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql db replica set-primary'] = """
type: command
short-summary: Set the primary replica database by failing over from the current primary replica database.
examples:
  - name: Set the primary replica database by failing over from the current primary replica database. (autogenerated)
    text: az sql db replica set-primary --allow-data-loss --name MyDatabase --resource-group MyResourceGroup --server myserver --subscription MySubscription
    crafted: true
"""

helps['sql db restore'] = """
type: command
short-summary: Create a new database by restoring from a backup.
examples:
  - name: Create a new database by restoring from a backup. (autogenerated)
    text: |
        az sql db restore --dest-name MyDest --edition GeneralPurpose --name MyAzureSQLDatabase --resource-group MyResourceGroup --server myserver --subscription MySubscription --time "2018-05-20T05:34:22"
    crafted: true
  - name: Create a new database with geo-redundant backup storage by restoring from a backup. (autogenerated)
    text: |
        az sql db restore --dest-name MyDest --edition GeneralPurpose --name MyAzureSQLDatabase --resource-group MyResourceGroup --server myserver --subscription MySubscription --time "2018-05-20T05:34:22" --backup-storage-redundancy Geo
"""

helps['sql db show'] = """
type: command
short-summary: Get the details for a database.
examples:
  - name: Get the details for a database. (autogenerated)
    text: az sql db show --name MyAzureSQLDatabase --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql db show-connection-string'] = """
type: command
short-summary: Generates a connection string to a database.
examples:
  - name: Generate connection string for ado.net
    text: az sql db show-connection-string -s myserver -n mydb -c ado.net
"""

helps['sql db tde'] = """
type: group
short-summary: Manage a database's transparent data encryption.
"""

helps['sql db tde set'] = """
type: command
short-summary: Sets a database's transparent data encryption configuration.
examples:
  - name: Sets a database's transparent data encryption configuration. (autogenerated)
    text: az sql db tde set --database mydb --resource-group MyResourceGroup --server myserver --status Enabled
    crafted: true
"""

helps['sql db threat-policy'] = """
type: group
short-summary: Manage a database's threat detection policies.
"""

helps['sql db threat-policy update'] = """
type: command
short-summary: Update a database's threat detection policy.
long-summary: If the policy is being enabled, storage_account or both storage_endpoint and storage_account_access_key must be specified.
examples:
  - name: Enable by storage account name.
    text: |
        az sql db threat-policy update -g mygroup -s myserver -n mydb \\
            --state Enabled --storage-account mystorage
  - name: Enable by storage endpoint and key.
    text: |
        az sql db threat-policy update -g mygroup -s myserver -n mydb \\
            --state Enabled --storage-endpoint https://mystorage.blob.core.windows.net \\
            --storage-key MYKEY==
  - name: Disable a subset of alert types.
    text: |
        az sql db threat-policy update -g mygroup -s myserver -n mydb \\
            --disabled-alerts Sql_Injection_Vulnerability Access_Anomaly
  - name: Configure email recipients for a policy.
    text: |
        az sql db threat-policy update -g mygroup -s myserver -n mydb \\
            --email-addresses me@examlee.com you@example.com \\
            --email-account-admins Enabled
  - name: Disable a threat policy.
    text: az sql db threat-policy update -g mygroup -s myserver -n mydb --state Disabled
"""

helps['sql db update'] = """
type: command
short-summary: Update a database.
examples:
  - name: Update a database to Standard edition, S0 performance level (10 DTU) by specifying DTU capacity. Note that GeneralPurpose allows a wider range of max size than Standard edition.
    text: az sql db update -g mygroup -s myserver -n mydb --edition Standard --capacity 10 --max-size 250GB
  - name: Update a database to Standard edition, S1 performance level (20 DTU) by specifying performance level name. Note that GeneralPurpose allows a wider range of max size than Standard edition.
    text: az sql db update -g mygroup -s myserver -n mydb --edition Standard --service-objective S1 --max-size 250GB
  - name: Update a database to GeneralPurpose edition, 4 vcores with Gen5 hardware
    text: az sql db update -g mygroup -s myserver -n mydb --edition GeneralPurpose --capacity 4 --family Gen5
  - name: Update database with increased max size
    text: az sql db update -g mygroup -s myserver -n mydb --max-size 500GB
  - name: Update database with zone redundancy enabled
    text: az sql db update -g mygroup -s myserver -n mydb -z
  - name: Update database with zone redundancy explicitly disabled
    text: az sql db update -g mygroup -s myserver -n mydb -z false
  - name: Update database to serverless compute model
    text: az sql db update -g mygroup -s myserver -n mydb --edition GeneralPurpose --capacity 2 --family Gen5 --compute-model Serverless
  - name: Update database with locally redundant backup storage
    text: az sql db update -g mygroup -s myserver -n mydb --backup-storage-redundancy Local

"""

helps['sql dw'] = """
type: group
short-summary: Manage data warehouses.
"""

helps['sql dw create'] = """
type: command
short-summary: Create a data warehouse.
examples:
  - name: Create a data warehouse. (autogenerated)
    text: az sql dw create --name MyDataWarehouse --resource-group MyResourceGroup --server myserver --service-objective S0
    crafted: true
"""

helps['sql dw delete'] = """
type: command
short-summary: Delete a data warehouse.
examples:
  - name: Delete a data warehouse. (autogenerated)
    text: az sql dw delete --name MyDataWarehouse --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql dw list'] = """
type: command
short-summary: List data warehouses for a server.
examples:
  - name: List data warehouses for a server. (autogenerated)
    text: az sql dw list --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql dw show'] = """
type: command
short-summary: Get the details for a data warehouse.
examples:
  - name: Get the details for a data warehouse. (autogenerated)
    text: az sql dw show --name MyDataWarehouse --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql dw update'] = """
type: command
short-summary: Update a data warehouse.
examples:
  - name: Update a data warehouse. (autogenerated)
    text: az sql dw update --name MyDataWarehouse --resource-group MyResourceGroup --server myserver --service-objective S1
    crafted: true
"""

helps['sql elastic-pool'] = """
type: group
short-summary: Manage elastic pools.
"""

helps['sql elastic-pool create'] = """
type: command
short-summary: Create an elastic pool.
examples:
  - name: Create elastic pool with zone redundancy enabled
    text: az sql elastic-pool create -g mygroup -s myserver -n mypool -z
  - name: Create elastic pool with zone redundancy explicitly disabled
    text: az sql elastic-pool create -g mygroup -s myserver -n mypool -z false
  - name: Create a Standard 100 DTU elastic pool.
    text: az sql elastic-pool create -g mygroup -s myserver -n mydb -e Standard -c 100
  - name: Create an elastic pool with GeneralPurpose edition, Gen4 hardware and 1 vcore.
    text: az sql elastic-pool create -g mygroup -s myserver -n mydb -e GeneralPurpose -f Gen4 -c 1
  - name: Create an elastic pool with Hyperscale edition, Gen5 hardware, 4 vcore and 2 high availability replicas.
    text: az sql elastic-pool create -g mygroup -s myserver -n mydb -e Hyperscale -f Gen5 -c 4 --ha-replicas 2
"""

helps['sql elastic-pool list-editions'] = """
type: command
short-summary: List elastic pool editions available for the active subscription.
long-summary: Also includes available pool DTU settings, storage limits, and per database settings. In order to reduce verbosity, additional storage limits and per database settings are hidden by default.
examples:
  - name: Show all elastic pool editions and pool DTU limits in the West US region.
    text: az sql elastic-pool list-editions -l westus -o table
  - name: Show all pool DTU limits for Standard edition in the West US region.
    text: az sql elastic-pool list-editions -l westus --edition Standard -o table
  - name: Show available max sizes for elastic pools with at least 100 DTUs in the West US region.
    text: az sql elastic-pool list-editions -l westus --dtu 100 --show-details max-size -o table
  - name: Show available per database settings for Standard 100 DTU elastic pools in the West US region.
    text: az sql elastic-pool list-editions -l westus --edition Standard --dtu 100 -o table --show-details db-min-dtu db-max-dtu db-max-size
"""

helps['sql elastic-pool op'] = """
type: group
short-summary: Manage operations on an elastic pool.
"""

helps['sql elastic-pool op cancel'] = """
type: command
examples:
  - name: Cancel an operation.
    text: az sql elastic-pool op cancel -g mygroup -s myserver --elastic-pool myelasticpool -n d2896mydb-2ba8-4c84-bac1-387c430cce40
"""

helps['sql elastic-pool update'] = """
type: command
short-summary: Update an elastic pool.
examples:
  - name: Update elastic pool with zone redundancy enabled
    text: az sql elastic-pool update -g mygroup -s myserver -n mypool -z
  - name: Update elastic pool with zone redundancy explicitly disabled
    text: az sql elastic-pool update -g mygroup -s myserver -n mypool -z false
  - name: Update elastic pool with 2 high availability replicas
    text: az sql elastic-pool update -g mygroup -s myserver -n mypool --ha-replicas 2
"""

helps['sql failover-group'] = """
type: group
short-summary: Manage SQL Failover Groups.
"""

helps['sql failover-group create'] = """
type: command
short-summary: Creates a failover group.
examples:
  - name: Creates a failover group. (autogenerated)
    text: az sql failover-group create --name MyFailoverGroup --partner-server newDb --resource-group MyResourceGroup --server myserver --subscription MySubscription
    crafted: true
"""

helps['sql failover-group set-primary'] = """
type: command
short-summary: Set the primary of the failover group by failing over all databases from the current primary server.
examples:
  - name: Set the primary of the failover group by failing over all databases from the current primary server. (autogenerated)
    text: az sql failover-group set-primary --name MyFailoverGroup --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql failover-group update'] = """
type: command
short-summary: Updates the failover group.
"""

helps['sql instance-failover-group'] = """
type: group
short-summary: Manage SQL Instance Failover Groups.
"""

helps['sql instance-failover-group create'] = """
type: command
short-summary: Creates an instance failover group between two connected managed instances.
long-summary: If an outage occurs on the primary server, the grace period indicates that Azure SQL Managed Database will not initiate automatic failover before the grace period expires. Please note that failover operation with --allow-data-loss option might cause data loss due to the nature of asynchronous synchronization.
"""

helps['sql instance-failover-group set-primary'] = """
type: command
short-summary: Set the primary of the instance failover group by failing over all databases from the current primary managed instance.
"""

helps['sql instance-failover-group update'] = """
type: command
short-summary: Updates the instance failover group.
"""

helps['sql instance-pool'] = """
type: group
short-summary: Manage instance pools.
"""

helps['sql instance-pool create'] = """
type: command
short-summary: Create an instance pool.
examples:
  - name: Example to create an instance pool (include --no-wait in the end to get an asynchronous experience)
    text: az sql instance-pool create -g resource_group_name -n instance_pool_name -l location --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName} --license-type LicenseIncluded --capacity 8 -e GeneralPurpose -f Gen5 --no-wait
  - name: Example to create an instance pool with subnet name and vnet-name
    text: az sql instance-pool create --license-type LicenseIncluded -l northcentralus -n myinstancepool -c 8 -e GeneralPurpose -f Gen5 -g billingPools --subnet mysubnetname --vnet-name myvnetname
"""

helps['sql instance-pool delete'] = """
type: command
short-summary: Delete an instance pool.
examples:
  - name: Delete an instance pool
    text: az sql instance-pool delete -g mygroup -n myinstancepool --yes
"""

helps['sql instance-pool list'] = """
type: command
short-summary: List available instance pools.
examples:
  - name: List all instance pools in the current subscription.
    text: az sql instance-pool list
  - name: List all instance pools in a resource group.
    text: az sql instance-pool list -g mygroup
"""

helps['sql instance-pool show'] = """
type: command
short-summary: Get the details for an instance pool.
examples:
  - name: Get the details for an instance pool
    text: az sql instance-pool show -g mygroup -n myinstancepool
"""

helps['sql instance-pool update'] = """
type: command
short-summary: Update an instance pool.
examples:
  - name: Update an instance pool with new tags (make sure they are space separated if there are multiple tags)
    text: az sql instance-pool update -n myinstancepool -g mygroup --tags mykey1=myvalue1 mykey2=myvalue2
  - name: Clear the tags assigned to an instance pool
    text: az sql instance-pool update -n myinstancepool -g mygroup --tags ""
"""

helps['sql instance-pool wait'] = """
type: command
short-summary: Wait for an instance pool to reach a desired state.
examples:
  - name: Wait until an instance pool gets created.
    text: az sql instance-pool wait -n myinstancepool -g mygroup --created
"""

helps['sql stg'] = """
type: group
short-summary: Manage Server Trust Groups.
"""

helps['sql stg create'] = """
type: command
short-summary: Create a Server Trust Group.
examples:
  - name: Create a Server Trust Group with specified resource ids of its members.
    text: az sql stg create -g resourcegroup -l location -n stg-name --trust-scope GlobalTransactions -m $mi1-id $mi2-id
"""

helps['sql stg show'] = """
type: command
short-summary: Retrieve a Server Trust Group.
examples:
  - name: Retrieve a Server Trust Group.
    text: az sql stg show -g resourcegroup -l location -n stg-name
"""

helps['sql stg delete'] = """
type: command
short-summary: Delete a Server Trust Group.
examples:
  - name: Delete a Server Trust Group.
    text: az sql stg delete -g resourcegroup -l location -n stg-name
"""

helps['sql stg list'] = """
type: command
short-summary: Retrieve a list of Server Trust Groups.
examples:
  - name: Retrieve a list of Server Trust Groups by instance.
    text: az sql stg list -g resourcegroup --instance-name mi1-name
  - name: Retrieve a list of Server Trust Groups by location.
    text: az sql stg list -g resourcegroup -l location
"""

helps['sql mi'] = """
type: group
short-summary: Manage SQL managed instances.
"""

helps['sql mi ad-admin'] = """
type: group
short-summary: Manage a managed instance's Active Directory administrator.
"""

helps['sql mi ad-admin create'] = """
type: command
short-summary: Creates a new managed instance Active Directory administrator.
"""

helps['sql mi ad-admin delete'] = """
type: command
short-summary: Deletes an existing managed instance Active Directory Administrator.
"""

helps['sql mi ad-admin list'] = """
type: command
short-summary: Returns a list of managed instance Active Directory Administrators.
"""

helps['sql mi ad-admin update'] = """
type: command
short-summary: Updates an existing managed instance Active Directory administrator.
"""

helps['sql mi ad-only-auth'] = """
type: group
short-summary: Manage a Managed Instance's Azure Active Directly only settings.
"""

helps['sql mi ad-only-auth enable'] = """
type: command
short-summary: Enable Azure Active Directly only Authentication for this Managed Instance.
examples:
  - name: Enable Active Directory only authentication for a managed instance
    text: az sql mi ad-only-auth enable --resource-group mygroup --name myMI
"""

helps['sql mi ad-only-auth disable'] = """
type: command
short-summary: Disable Azure Active Directly only Authentication for this Managed Instance.
examples:
  - name: Disable Active Directory only authentication for a managed instance
    text: az sql mi ad-only-auth disable --resource-group mygroup --name myMI
"""

helps['sql mi ad-only-auth get'] = """
type: command
short-summary: Get a specific Azure Active Directly only Authentication property.
examples:
  - name: Get Active Directory only authentication status for a managed instance
    text: az sql mi ad-only-auth get --resource-group mygroup --name myMI
"""

helps['sql mi create'] = """
type: command
short-summary: Create a managed instance.
examples:
  - name: Create a managed instance with minimal set of parameters
    text: az sql mi create -g mygroup -n myinstance -l mylocation -i -u myusername -p mypassword --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName}
  - name: Create a managed instance with specified parameters and with identity
    text: az sql mi create -g mygroup -n myinstance -l mylocation -i -u myusername -p mypassword --license-type LicenseIncluded --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName} --capacity 8 --storage 32GB --edition GeneralPurpose --family Gen5
  - name: Create managed instance with specified parameters and tags
    text: az sql mi create -g mygroup -n myinstance -l mylocation -i -u myusername -p mypassword --license-type LicenseIncluded --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName} --capacity 8 --storage 32GB --edition GeneralPurpose --family Gen5 --tags tagName1=tagValue1 tagName2=tagValue2
  - name: Create managed instance with specified parameters and backup storage redundancy specified
    text: az sql mi create -g mygroup -n myinstance -l mylocation -i -u myusername -p mypassword --license-type LicenseIncluded --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName} --capacity 8 --storage 32GB --edition GeneralPurpose --family Gen5 --backup-storage-redundancy Local
  - name: Create a managed instance with maintenance configuration
    text: az sql mi create -g mygroup -n myinstance -l mylocation -i -u myusername -p mypassword --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName} -m SQL_{Region}_{MaintenanceConfigName}
  - name: Create a managed instance with Service Principal enabled
    text: az sql mi create -g mygroup -n myinstance -l mylocation -i -u myusername -p mypassword --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName} --service-principal-type SystemAssigned
  - name: Create a managed instance without SQL Admin, with AAD admin and AD Only enabled
    text: az sql mi create --enable-ad-only-auth --external-admin-principal-type User --external-admin-name myUserName --external-admin-sid c5e964e2-6bb2-2222-1111-3b16ec0e1234 -g myResourceGroup -n miName --subnet /subscriptions/78975f9f-2222-1111-1111-29c42ac70000/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet-test/subnets/ManagedInstance
  - name: Create a managed instance without SQL Admin, with AD admin, AD Only enabled, User ManagedIdenties and Identity Type is SystemAssigned,UserAssigned.
    text: az sql mi create --enable-ad-only-auth --external-admin-principal-type User --external-admin-name myUserName \\
              --external-admin-sid c5e964e2-6bb2-1111-1111-3b16ec0e1234 -g myResourceGroup -n myServer -i \\
              --user-assigned-identity-id /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
              --identity-type SystemAssigned,UserAssigned --pid /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
              --subnet /subscriptions/78975f9f-2222-1111-1111-29c42ac70000/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet-test/subnets/ManagedInstance
  - name: Create a managed instance without SQL Admin, with AD admin, AD Only enabled, User ManagedIdenties and Identity Type is UserAssigned.
    text: az sql mi create --enable-ad-only-auth --external-admin-principal-type User --external-admin-name myUserName \\
              --external-admin-sid c5e964e2-6bb2-1111-1111-3b16ec0e1234 -g myResourceGroup -n myServer -i \\
              --user-assigned-identity-id /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
              --identity-type UserAssigned --pid /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
              --subnet /subscriptions/78975f9f-2222-1111-1111-29c42ac70000/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet-test/subnets/ManagedInstance
"""

helps['sql mi delete'] = """
type: command
short-summary: Delete a managed instance.
examples:
  - name: Delete a managed instance
    text: az sql mi delete -g mygroup -n myinstance --yes
"""

helps['sql mi failover'] = """
type: command
short-summary: Failover a managed instance.
examples:
  - name: Failover a managed instance primary replica
    text: az sql mi failover -g mygroup -n myinstance
  - name: Failover a managed instance readable secodary replica
    text: az sql mi failover -g mygroup -n myinstance --replica-type ReadableSecondary
"""

helps['sql mi key'] = """
type: group
short-summary: Manage a SQL Instance's keys.
"""

helps['sql mi key create'] = """
type: command
short-summary: Creates a SQL Instance key.
"""

helps['sql mi key delete'] = """
type: command
short-summary: Deletes a SQL Instance key.
"""

helps['sql mi key show'] = """
type: command
short-summary: Shows a SQL Instance key.
"""

helps['sql mi list'] = """
type: command
short-summary: List available managed instances.
examples:
  - name: List all managed instances in the current subscription.
    text: az sql mi list
  - name: List all managed instances in a resource group.
    text: az sql mi list -g mygroup
"""

helps['sql mi op'] = """
type: group
short-summary: Manage operations on a managed instance.
"""

helps['sql mi show'] = """
type: command
short-summary: Get the details for a managed instance.
examples:
  - name: Get the details for a managed instance
    text: az sql mi show -g mygroup -n myinstance
"""

helps['sql mi tde-key'] = """
type: group
short-summary: Manage a SQL Instance's encryption protector.
"""

helps['sql mi tde-key set'] = """
type: command
short-summary: Sets the SQL Instance's encryption protector.
"""

helps['sql mi update'] = """
type: command
short-summary: Update a managed instance.
examples:
  - name: Updates a mi with specified parameters and with identity
    text: az sql mi update -g mygroup -n myinstance -i -p mypassword --license-type mylicensetype --capacity vcorecapacity --storage storagesize
  - name: Update mi edition and hardware family
    text: az sql mi update -g mygroup -n myinstance --tier GeneralPurpose --family Gen5
  - name: Add or update a tag.
    text: az sql mi update -g mygroup -n myinstance --set tags.tagName=tagValue
  - name: Remove a tag.
    text: az sql mi update -g mygroup -n myinstance --remove tags.tagName
  - name: Update a managed instance. (autogenerated)
    text: az sql mi update --name myinstance --proxy-override Default --resource-group mygroup --subscription MySubscription
    crafted: true
  - name: Update a managed instance. (autogenerated)
    text: az sql mi update --name myinstance --public-data-endpoint-enabled true --resource-group mygroup --subscription MySubscription
    crafted: true
  - name: Update a managed instance with maintenance configuration
    text: az sql mi update -g mygroup -n myinstance -m SQL_{Region}_{MaintenanceConfigName}
  - name: Remove maintenance configuration from managed instance
    text: az sql mi update -g mygroup -n myinstance -m SQL_Default
  - name: Update a managed instance with Service Principal
    text: az sql mi update -g mygroup -n myinstance --service-principal-type SystemAssigned
  - name: Update a managed instance with User Managed Identies and Identity Type is SystemAssigned,UserAssigned.
    text: az sql mi update -g myResourceGroup -n myServer -i \\
              --user-assigned-identity-id /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
              --identity-type SystemAssigned,UserAssigned --pid /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi
  - name: Update a managed instance with User Managed Identies and Identity Type is UserAssigned
    text: az sql mi update -g myResourceGroup -n myServer -i \\
              --user-assigned-identity-id /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
              --identity-type UserAssigned --pid /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi
  - name: Move managed instance to another subnet
    text: az sql mi update -g myResourceGroup -n myServer -i \\
              --subnet /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
  - name: Update mi backup storage redundancy
    text: az sql mi update -g mygroup -n myinstance --bsr Local
"""

helps['sql midb'] = """
type: group
short-summary: Manage SQL managed instance databases.
"""

helps['sql midb create'] = """
type: command
short-summary: Create a managed database.
examples:
  - name: Create a managed database with specified collation
    text: az sql midb create -g mygroup --mi myinstance -n mymanageddb --collation Latin1_General_100_CS_AS_SC
"""

helps['sql midb update'] = """
type: command
short-summary: Update a managed database.
examples:
  - name: Update a managed database with specified tags
    text: az sql midb update -g mygroup --mi myinstance -n mymanageddb --tags tag1="value1"
"""

helps['sql midb delete'] = """
type: command
short-summary: Delete a managed database.
examples:
  - name: Delete a managed database
    text: az sql midb delete -g mygroup --mi myinstance -n mymanageddb --yes
"""

helps['sql midb list'] = """
type: command
short-summary: List managed databases on a managed instance.
examples:
  - name: List managed databases on a managed instance
    text: az sql midb list -g mygroup --mi myinstance
"""

helps['sql midb list-deleted'] = """
type: command
short-summary: List restorable deleted managed databases.
examples:
  - name: List all restorable deleted managed databases on Managed Instance .
    text: az sql midb list-deleted -g mygroup --mi myinstance
"""

helps['sql midb restore'] = """
type: command
short-summary: Restore a managed database.
examples:
  - name: Restore a live managed database using Point in time restore
    text: az sql midb restore -g mygroup --mi myinstance -n mymanageddb --dest-name targetmidb --time "2018-05-20T05:34:22"
  - name: Restore a dropped managed database using Point in time restore
    text: az sql midb restore -g mygroup --mi myinstance -n mymanageddb --dest-name targetmidb --time "2018-05-20T05:34:22" --deleted-time "2018-05-20T05:34:22"
  - name: Restore a live managed database from another instance using Point in time restore
    text: az sql midb restore -g mygroup --mi myinstance -n mymanageddb --dest-name targetmidb --time "2018-05-20T05:34:22" --dest-mi targetmi --dest-resource-group targetrg
"""

helps['sql midb show'] = """
type: command
short-summary: Get the details for a managed database.
examples:
  - name: Get the details for a managed database
    text: az sql midb show -g mygroup --mi myinstance -n mymanageddb
"""

helps['sql midb short-term-retention-policy'] = """
type: group
short-summary: Manage SQL Managed Instance database backup short term retention policy.
"""

helps['sql midb short-term-retention-policy set'] = """
type: command
short-summary: Update short term retention for automated backups on a single database.
examples:
  - name: Set backup short term retention for live managed database.
    text: az sql midb short-term-retention-policy set -g mygroup --mi myinstance -n mymanageddb --retention-days retentionindays
  - name: Set backup short term retention for dropped managed database.
    text: az sql midb short-term-retention-policy set -g mygroup --mi myinstance -n mymanageddb --deleted-time "2018-05-20T05:34:22" --retention-days retentionindays
"""

helps['sql midb short-term-retention-policy show'] = """
type: command
short-summary: Show short term retention for automated backups on a single database.
examples:
  - name: Shows backup short term retention for live managed database.
    text: az sql midb short-term-retention-policy show -g mygroup --mi myinstance -n mymanageddb
  - name: Show backup short term retention for dropped managed database.
    text: az sql midb short-term-retention-policy show -g mygroup --mi myinstance -n mymanageddb --deleted-time "2018-05-20T05:34:22"
"""

helps['sql midb ltr-policy'] = """
type: group
short-summary: Manage SQL Managed Instance database long term retention policy.
"""

helps['sql midb ltr-policy set'] = """
type: command
short-summary: Update long term retention settings for a managed database.
examples:
  - name: Set long term retention for a managed database.
    text: az sql midb ltr-policy set -g mygroup --mi myinstance -n mymanageddb --weekly-retention "P1W" --monthly-retention "P6M" --yearly-retention "P1Y" --week-of-year 26
"""

helps['sql midb ltr-policy show'] = """
type: command
short-summary: Show the long term retention policy for a managed database.
examples:
  - name: Show long term retention policy for a managed database.
    text: az sql midb ltr-policy show -g mygroup --mi myinstance -n mymanageddb
"""

helps['sql midb ltr-backup'] = """
type: group
short-summary: Manage SQL Managed Instance database long term retention backups.
"""

helps['sql midb ltr-backup show'] = """
type: command
short-summary: Get a long term retention backup for a managed database.
examples:
  - name: Show long term retention backup for a managed database.
    text: az sql midb ltr-backup show -l southeastasia --mi myinstance -d mymanageddb -n "3214b3fb-fba9-43e7-96a3-09e35ffcb336;132292152080000000"
    name: Show long term retention backup for a managed database.
    text: az sql midb ltr-backup show --backup-id '/subscriptions/6caa113c-794c-42f8-ab9d-878d8aa104dc/resourceGroups/mygroup/providers/Microsoft.Sql/locations/southeastasia/longTermRetentionManagedInstances/myinstance/longTermRetentionDatabases/mymanageddb/longTermRetentionManagedInstanceBackups/3214b3fb-fba9-43e7-96a3-09e35ffcb336;132292152080000000'
"""

helps['sql midb ltr-backup list'] = """
type: command
short-summary: List the long term retention backups for a location, instance or database.
examples:
  - name: List long term retention backups for a managed database.
    text: az sql midb ltr-backup list -l southeastasia --mi myinstance -d mymanageddb
  - name: List long term retention backups for a managed instance (list only the latest LTR backups, which belong to live databases).
    text: az sql midb ltr-backup list -l southeastasia --mi myinstance --database-state Live --only-latest-per-database
  - name: List long term retention backups for a managed instance (with resource group argument).
    text: az sql midb ltr-backup list -l southeastasia -g mygroup --mi myinstance
  - name: List long term retention backups for a location (list only the latest LTR backups, which belong to live databases).
    text: az sql midb ltr-backup list -l southeastasia --database-state Live --only-latest-per-database
  - name: List long term retention backups for a location (with resource group argument).
    text: az sql midb ltr-backup list -l southeastasia -g mygroup
"""

helps['sql midb ltr-backup delete'] = """
type: command
short-summary: Delete a long term retention backup.
examples:
  - name: Delete long term retention backup for a managed database.
    text: az sql midb ltr-backup delete -l southeastasia --mi myinstance -d mymanageddb --name "3214b3fb-fba9-43e7-96a3-09e35ffcb336;132292152080000000"
  - name: Delete long term retention backup for a managed database.
    text: az sql midb ltr-backup delete --backup-id '/subscriptions/6caa113c-794c-42f8-ab9d-878d8aa104dc/resourceGroups/mygroup/providers/Microsoft.Sql/locations/southeastasia/longTermRetentionManagedInstances/myinstance/longTermRetentionDatabases/mymanageddb/longTermRetentionManagedInstanceBackups/3214b3fb-fba9-43e7-96a3-09e35ffcb336;132292152080000000'
"""

helps['sql midb ltr-backup restore'] = """
type: command
short-summary: Restore a long term retention backup to a new database.
examples:
  - name: Restore a managed database using LTR backup.
    text: |
            az sql midb ltr-backup restore \\
                --dest-database targetmidb --dest-mi myinstance --dest-resource-group mygroup \\
                --backup-id "/subscriptions/6caa113c-794c-42f8-ab9d-878d8aa104dc/resourceGroups/mygroup/providers/Microsoft.Sql/locations/southeastasia/longTermRetentionManagedInstances/myinstance/longTermRetentionDatabases/sourcemidb/longTermRetentionManagedInstanceBackups/3214b3fb-fba9-43e7-96a3-09e35ffcb336;132292152080000000"
"""

helps['sql midb ltr-backup wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the managed database is met.
"""

helps['sql midb log-replay'] = """
type: group
short-summary: SQL Managed Instance database Log Replay service commands.
"""

helps['sql midb log-replay start'] = """
type: command
short-summary: Start Log Replay service on specified database.
examples:
  - name: Start Log Replay service with auto complete option.
    text: az sql midb log-replay start -g mygroup --mi myinstance -n mymanageddb -a --last-bn "backup.bak" --storage-uri "https://test.blob.core.windows.net/testing" --storage-sas "sv=2019-02-02&ss=b&srt=sco&sp=rl&se=2023-12-02T00:09:14Z&st=2019-11-25T16:09:14Z&spr=https&sig=92kAe4QYmXaht%2Fgjocqwerqwer41s%3D"
  - name: Start Log Replay service without auto complete option.
    text: az sql midb log-replay start -g mygroup --mi myinstance -n mymanageddb --storage-uri "https://test.blob.core.windows.net/testing" --storage-sas "sv=2019-02-02&ss=b&srt=sco&sp=rl&se=2023-12-02T00:09:14Z&st=2019-11-25T16:09:14Z&spr=https&sig=92kAe4QYmXaht%2Fgjocqwerqwer41s%3D"
"""

helps['sql midb log-replay complete'] = """
type: command
short-summary: Complete Log Replay service on specified database.
examples:
  - name: Complete log replay service.
    text: az sql midb log-replay complete -g mygroup --mi myinstance -n mymanageddb --last-backup-name "backup.bak"
"""

helps['sql midb log-replay show'] = """
type: command
short-summary: Get status of Log Replay service.
examples:
  - name: Get status of the ongoing log replay service.
    text: az sql midb log-replay show -g mygroup --mi myinstance -n mymanageddb
"""

helps['sql midb log-replay stop'] = """
type: command
short-summary: Stop Log Replay service.
examples:
  - name: Stop ongoing log replay service by deleting database.
    text: az sql midb log-replay stop -g mygroup --mi myinstance -n mymanageddb
"""

helps['sql midb log-replay wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the managed database is met.
examples:
  - name: Place the CLI in a waiting state until a condition of the managed database is met after starting log replay service.
    text: az sql midb log-replay wait --exists --resource-group mygroup --managed-instance myinstance --name mymanageddb
  - name: Place the CLI in a waiting state until a condition of the managed database is met after stopping log replay service.
    text: az sql midb log-replay wait --deleted --resource-group mygroup --managed-instance myinstance --name mymanageddb
"""

helps['sql server'] = """
type: group
short-summary: Manage SQL servers.
"""

helps['sql server ad-admin'] = """
type: group
short-summary: Manage a server's Active Directory administrator.
"""

helps['sql server ad-admin create'] = """
type: command
short-summary: Create a new server Active Directory administrator.
"""

helps['sql server ad-admin update'] = """
type: command
short-summary: Update an existing server Active Directory administrator.
"""

helps['sql server ad-only-auth'] = """
type: group
short-summary: Manage Azure Active Directly only Authentication settings for this Server.
"""

helps['sql server ad-only-auth enable'] = """
type: command
short-summary: Enable Azure Active Directly only Authentication for this Server.
examples:
  - name: Enable Active Directory only authentication for a sql server
    text: az sql server ad-only-auth enable --resource-group mygroup --name myServer
"""

helps['sql server ad-only-auth disable'] = """
type: command
short-summary: Disable Azure Active Directly only Authentication for this Server.
examples:
  - name: Disable Active Directory only authentication for a sql server
    text: az sql server ad-only-auth disable --resource-group mygroup --name myServer
"""

helps['sql server ad-only-auth get'] = """
type: command
short-summary: Get a specific Azure Active Directly only Authentication property.
examples:
  - name: Get Active Directory only authentication status for a sql server
    text: az sql server ad-only-auth get --resource-group mygroup --name myServer
"""

helps['sql server audit-policy'] = """
type: group
short-summary: Manage a server's auditing policy.
"""

helps['sql server audit-policy wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the server's audit policy is met.
examples:
  - name: Place the CLI in a waiting state until it determines that server's audit policy exists
    text: az sql server audit-policy wait -g mygroup -n myserver --exists
"""

helps['sql server audit-policy update'] = """
type: command
short-summary: Update a server's auditing policy.
long-summary: If the policy is being enabled, `--storage-account` or both `--storage-endpoint` and `--storage-key` must be specified.
examples:
  - name: Enable by storage account name.
    text: |
        az sql server audit-policy update -g mygroup -n myserver --state Enabled \\
            --bsts Enabled --storage-account mystorage
  - name: Enable by storage endpoint and key.
    text: |
        az sql server audit-policy update -g mygroup -n myserver --state Enabled \\
            --bsts Enabled --storage-endpoint https://mystorage.blob.core.windows.net \\
            --storage-key MYKEY==
  - name: Set the list of audit actions.
    text: |
        az sql server audit-policy update -g mygroup -n myserver \\
            --actions FAILED_DATABASE_AUTHENTICATION_GROUP 'UPDATE on server::myserver by public'
  - name: Disable an auditing policy.
    text: az sql server audit-policy update -g mygroup -n myserver --state Disabled
  - name: Disable a blob storage auditing policy.
    text: az sql server audit-policy update -g mygroup -n myserver --bsts Disabled
  - name: Enable a log analytics auditing policy.
    text: |
        az sql server audit-policy update -g mygroup -n myserver --state Enabled \\
            --lats Enabled --lawri myworkspaceresourceid
  - name: Disable a log analytics auditing policy.
    text: |
        az sql server audit-policy update -g mygroup -n myserver
            --lats Disabled
  - name: Enable an event hub auditing policy.
    text: |
        az sql server audit-policy update -g mygroup -n myserver --state Enabled \\
            --event-hub-target-state Enabled \\
            --event-hub-authorization-rule-id eventhubauthorizationruleid \\
            --event-hub eventhubname
  - name: Enable an event hub auditing policy for default event hub.
    text: |
        az sql server audit-policy update -g mygroup -n myserver --state Enabled \\
            --event-hub-target-state Enabled \\
            --event-hub-authorization-rule-id eventhubauthorizationruleid
  - name: Disable an event hub auditing policy.
    text: |
        az sql server audit-policy update -g mygroup -n myserver
            --event-hub-target-state Disabled
"""

helps['sql server ms-support'] = """
type: group
short-summary: Manage a server's Microsoft support operations.
"""

helps['sql server ms-support audit-policy'] = """
type: group
short-summary: Manage a server's Microsoft support operations auditing policy.
"""

helps['sql server ms-support audit-policy wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the server's Microsoft support operations audit policy is met.
examples:
  - name: Place the CLI in a waiting state until it determines that server's Microsoft support operations audit policy exists
    text: az sql server ms-support audit-policy wait -g mygroup -n myserver --exists
"""

helps['sql server ms-support audit-policy update'] = """
type: command
short-summary: Update a server's Microsoft support operations auditing policy.
long-summary: If the Microsoft support operations policy is being enabled, `--storage-account` or both `--storage-endpoint` and `--storage-key` must be specified.
examples:
  - name: Enable by storage account name.
    text: |
        az sql server ms-support audit-policy update -g mygroup -n myserver --state Enabled \\
            --bsts Enabled --storage-account mystorage
  - name: Enable by storage endpoint and key.
    text: |
        az sql server ms-support audit-policy update -g mygroup -n myserver --state Enabled \\
            --bsts Enabled --storage-endpoint https://mystorage.blob.core.windows.net \\
            --storage-key MYKEY==
  - name: Disable a Microsoft support operations auditing policy.
    text: az sql server ms-support audit-policy update -g mygroup -n myserver --state Disabled
  - name: Disable a blob storage Microsoft support operations auditing policy.
    text: az sql server ms-support audit-policy update -g mygroup -n myserver --bsts Disabled
  - name: Enable a log analytics Microsoft support operations auditing policy.
    text: |
        az sql server ms-support audit-policy update -g mygroup -n myserver --state Enabled \\
            --lats Enabled --lawri myworkspaceresourceid
  - name: Disable a log analytics Microsoft support operations auditing policy.
    text: |
        az sql server ms-support audit-policy update -g mygroup -n myserver
            --lats Disabled
  - name: Enable an event hub Microsoft support operations auditing policy.
    text: |
        az sql server ms-support audit-policy update -g mygroup -n myserver --state Enabled \\
            --event-hub-target-state Enabled \\
            --event-hub-authorization-rule-id eventhubauthorizationruleid \\
            --event-hub eventhubname
  - name: Enable an event hub Microsoft support operations auditing policy for default event hub.
    text: |
        az sql server ms-support audit-policy update -g mygroup -n myserver --state Enabled \\
            --event-hub-target-state Enabled \\
            --event-hub-authorization-rule-id eventhubauthorizationruleid
  - name: Disable an event hub Microsoft support operations auditing policy.
    text: |
        az sql server ms-support audit-policy update -g mygroup -n myserver
            --event-hub-target-state Disabled
"""

helps['sql server conn-policy'] = """
type: group
short-summary: Manage a server's connection policy.
"""

helps['sql server conn-policy show'] = """
type: command
short-summary: Gets a server's secure connection policy.
examples:
  - name: Gets a server's secure connection policy. (autogenerated)
    text: az sql server conn-policy show --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql server conn-policy update'] = """
type: command
short-summary: Updates a server's secure connection policy.
examples:
  - name: Updates a server's secure connection policy. (autogenerated)
    text: az sql server conn-policy update --connection-type Default --resource-group MyResourceGroup --server myserver
    crafted: true
"""

helps['sql server create'] = """
type: command
short-summary: Create a server.
examples:
  - name: Create a server.
    text: az sql server create -l westus -g mygroup -n myserver -u myadminuser -p myadminpassword
  - name: Create a server with disabled public network access to server.
    text: az sql server create -l westus -g mygroup -n myserver -u myadminuser -p myadminpassword -e false
  - name: Create a server without SQL Admin, with AD admin and AD Only enabled.
    text: az sql server create --enable-ad-only-auth --external-admin-principal-type User --external-admin-name myUserName --external-admin-sid c5e964e2-6bb2-1111-1111-3b16ec0e1234 -g myResourceGroup -n myServer
  - name: Create a server without SQL Admin, with AD admin, AD Only enabled, User ManagedIdenties and Identity Type is SystemAssigned,UserAssigned.
    text: az sql server create --enable-ad-only-auth --external-admin-principal-type User --external-admin-name myUserName \\
              --external-admin-sid c5e964e2-6bb2-1111-1111-3b16ec0e1234 -g myResourceGroup -n myServer -i \\
              --user-assigned-identity-id /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
              --identity-type SystemAssigned,UserAssigned --pid /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi
  - name: Create a server without SQL Admin, with AD admin, AD Only enabled, User ManagedIdenties and Identity Type is UserAssigned.
    text: az sql server create --enable-ad-only-auth --external-admin-principal-type User --external-admin-name myUserName \\
              --external-admin-sid c5e964e2-6bb2-1111-1111-3b16ec0e1234 -g myResourceGroup -n myServer -i \\
              --user-assigned-identity-id /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
              --identity-type UserAssigned --pid /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi
"""

helps['sql server dns-alias'] = """
type: group
short-summary: Manage a server's DNS aliases.
"""

helps['sql server dns-alias set'] = """
type: command
short-summary: Sets a server to which DNS alias should point
"""

helps['sql server firewall-rule'] = """
type: group
short-summary: Manage a server's firewall rules.
"""

helps['sql server firewall-rule create'] = """
type: command
short-summary: Create a firewall rule.
examples:
  - name: Create a firewall rule
    text: az sql server firewall-rule create -g mygroup -s myserver -n myrule --start-ip-address 1.2.3.4 --end-ip-address 5.6.7.8
  - name: Create a firewall rule that allows access from Azure services
    text: az sql server firewall-rule create -g mygroup -s myserver -n myrule --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
"""

helps['sql server firewall-rule list'] = """
type: command
short-summary: List a server's firewall rules.
examples:
  - name: List a server's firewall rules
    text: az sql server firewall-rule list -g mygroup -s myserver
"""

helps['sql server firewall-rule show'] = """
type: command
short-summary: Shows the details for a firewall rule.
examples:
  - name: Show a firewall rule
    text: az sql server firewall-rule show -g mygroup -s myserver -n myrule
"""

helps['sql server firewall-rule update'] = """
type: command
short-summary: Update a firewall rule.
examples:
  - name: Update a firewall rule
    text: az sql server firewall-rule update -g mygroup -s myserver -n myrule --start-ip-address 5.4.3.2 --end-ip-address 9.8.7.6
"""

helps['sql server outbound-firewall-rule'] = """
type: group
short-summary: Manage a server's outbound firewall rules.
"""

helps['sql server outbound-firewall-rule create'] = """
type: command
short-summary: Create a new outbound firewall rule.
examples:
  - name: Create a new outbound firewall rule
    text: az sql server outbound-firewall-rule create -g mygroup -s myserver -n allowedFQDN
  - name: Create a new outbound firewall rule
    text: az sql server outbound-firewall-rule create -g mygroup -s myserver --outbound-rule-fqdn allowedFQDN
"""

helps['sql server outbound-firewall-rule list'] = """
type: command
short-summary: List a server's outbound firewall rules.
examples:
  - name: List a server's outbound firewall rules
    text: az sql server outbound-firewall-rule list -g mygroup -s myserver
"""

helps['sql server outbound-firewall-rule show'] = """
type: command
short-summary: Show the details for an outbound firewall rule.
examples:
  - name: Show the outbound firewall rule
    text: az sql server outbound-firewall-rule show -g mygroup -s myserver -n myrule
  - name: Show the outbound firewall rule
    text: az sql server outbound-firewall-rule show -g mygroup -s myserver --outbound-rule-fqdn allowedFQDN
"""

helps['sql server outbound-firewall-rule delete'] = """
type: command
short-summary: Delete the outbound firewall rule.
examples:
  - name: Delete the outbound firewall rule
    text: az sql server outbound-firewall-rule delete -g mygroup -s myserver -n myrule
  - name: Delete the outbound firewall rule
    text: az sql server outbound-firewall-rule delete -g mygroup -s myserver --outbound-rule-fqdn allowedFQDN
"""

helps['sql server key'] = """
type: group
short-summary: Manage a server's keys.
"""

helps['sql server key create'] = """
type: command
short-summary: Creates a server key.
"""

helps['sql server key delete'] = """
type: command
short-summary: Deletes a server key.
"""

helps['sql server key show'] = """
type: command
short-summary: Shows a server key.
"""

helps['sql server list'] = """
type: command
short-summary: List available servers.
examples:
  - name: List all servers in the current subscription.
    text: az sql server list
  - name: List all servers in a resource group.
    text: az sql server list -g mygroup
"""

helps['sql server tde-key'] = """
type: group
short-summary: Manage a server's encryption protector.
"""

helps['sql server tde-key set'] = """
type: command
short-summary: Sets the server's encryption protector.
"""

helps['sql server update'] = """
type: command
short-summary: Update a server.
examples:
  - name: Update a server. (autogenerated)
    text: az sql server update --admin-password myadminpassword --name MyAzureSQLServer --resource-group MyResourceGroup
    crafted: true
  - name: Update a server with User Managed Identies and Identity Type is SystemAssigned,UserAssigned.
    text: az sql server update -g myResourceGroup -n myServer -i \\
              --user-assigned-identity-id /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
              --identity-type SystemAssigned,UserAssigned --pid /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi
  - name: Update a server with User Managed Identies and Identity Type is UserAssigned.
    text: az sql server update -g myResourceGroup -n myServer -i \\
              --user-assigned-identity-id /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi \\
              --identity-type UserAssigned --pid /subscriptions/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/testumi
"""

helps['sql server vnet-rule'] = """
type: group
short-summary: Manage a server's virtual network rules.
"""

helps['sql server vnet-rule create'] = """
type: command
short-summary: Create a virtual network rule to allows access to an Azure SQL server.

examples:
  - name: Create a vnet rule by providing the subnet id.
    text: |
        az sql server vnet-rule create --server MyAzureSqlServer --name MyVNetRule \\
          -g MyResourceGroup --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName}
  - name: Create a vnet rule by providing the vnet and subnet name. The subnet id is created by taking the resource group name and subscription id of the SQL server.
    text: |
        az sql server vnet-rule create --server MyAzureSqlServer --name MyVNetRule \\
            -g MyResourceGroup --subnet subnetName --vnet-name vnetName
"""

helps['sql server vnet-rule update'] = """
type: command
short-summary: Update a virtual network rule.
"""

helps['sql server wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the SQL server is met.
"""

helps['sql virtual-cluster'] = """
type: group
short-summary: Manage SQL virtual clusters.
"""

helps['sql virtual-cluster delete'] = """
type: command
short-summary: Delete a virtual cluster.
examples:
  - name: Delete a virtual cluster
    text: az sql virtual-cluster delete -g mygroup -n mycluster
"""

helps['sql virtual-cluster list'] = """
type: command
short-summary: List available virtual clusters.
examples:
  - name: List all virtual clusters in the current subscription.
    text: az sql virtual-cluster list
  - name: List all virtual clusters in a resource group.
    text: az sql virtual-cluster list -g mygroup
"""

helps['sql virtual-cluster show'] = """
type: command
short-summary: Get the details for a virtual cluster.
examples:
  - name: Get the details for a virtual cluster
    text: az sql virtual-cluster show -g mygroup -n mycluster
"""

helps['sql db classification'] = """
type: group
short-summary: Manage sensitivity classifications.
"""

helps['sql db classification update'] = """
type: command
short-summary: Update a columns's sensitivity classification.
examples:
  - name: Update sensitivity classification for a given column.
    text: az sql db classification update -g mygroup -s myserver -n mydb --schema dbo --table mytable --column mycolumn --information-type Name --label "Confidential - GDPR"
"""

helps['sql db classification list'] = """
type: command
short-summary: Get the sensitivity classifications of a given database.
examples:
  - name: List the sensitivity classification of a given database.
    text: az sql db classification list -g mygroup -s myserver -n mydb
"""

helps['sql db classification show'] = """
type: command
short-summary: Get the sensitivity classification of a given column.
examples:
  - name: Get the sensitivity classification of a given column.
    text: az sql db classification show -g mygroup -s myserver -n mydb --schema dbo --table mytable --column mycolumn
"""

helps['sql db classification delete'] = """
type: command
short-summary: Delete the sensitivity classification of a given column.
examples:
  - name: Delete the sensitivity classification of a given column.
    text: az sql db classification delete -g mygroup -s myserver -n mydb --schema dbo --table mytable --column mycolumn
"""

helps['sql db classification recommendation'] = """
type: group
short-summary: Manage sensitivity classification recommendations.
"""

helps['sql db classification recommendation list'] = """
type: command
short-summary: List the recommended sensitivity classifications of a given database.
examples:
  - name: List the recommended sensitivity classifications of a given database.
    text: az sql db classification recommendation list -g mygroup -s myserver -n mydb
"""

helps['sql db classification recommendation enable'] = """
type: command
short-summary: Enable sensitivity recommendations for a given column (recommendations are enabled by default on all columns).
examples:
  - name: Enable sensitivity recommendations for a given column.
    text: az sql db classification recommendation enable -g mygroup -s myserver -n mydb --schema dbo --table mytable --column mycolumn
"""

helps['sql db classification recommendation disable'] = """
type: command
short-summary: Disable sensitivity recommendations for a given column (recommendations are enabled by default on all columns).
examples:
  - name: Disable sensitivity recommendations for a given column.
    text: az sql db classification recommendation disable -g mygroup -s myserver -n mydb --schema dbo --table mytable --column mycolumn
"""

helps['sql db ledger-digest-uploads'] = """
type: group
short-summary: Manage ledger digest upload settings.
"""

helps['sql db ledger-digest-uploads enable'] = """
type: command
short-summary: Enable uploading ledger digests to an Azure Storage account or to Azure Confidential Ledger. If uploading ledger digests is already enabled, the cmdlet resets the digest storage endpoint to a new value.
examples:
  - name: Enable uploading ledger digests to an Azure Blob storage.
    text: az sql db ledger-digest-uploads enable --name mydb --resource-group MyResourceGroup --server myserver --endpoint https://mystorage.blob.core.windows.net
"""

helps['sql db ledger-digest-uploads disable'] = """
type: command
short-summary: Disable uploading ledger digests.
examples:
  - name: Disable uploading ledger digests.
    text: az sql db ledger-digest-uploads disable --name mydb --resource-group MyResourceGroup --server myserver
"""

helps['sql db ledger-digest-uploads show'] = """
type: command
short-summary: Show the current ledger digest settings.
examples:
  - name: Show the settings for uploading ledger digests.
    text: az sql db ledger-digest-uploads show --name mydb --resource-group MyResourceGroup --server myserver
"""
