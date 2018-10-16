# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


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
    short-summary: Create a copy of a database.
    long-summary: A full list of performance level options can be seen by executing `az sql db list-editions -a -o table -l LOCATION`.
                  The copy destination database must have the same edition as the source database, but you can change the edition
                  after the copy has completed.
    examples:
        - name: Create a database with performance level S0 as a copy of an existing Standard database.
          text: az sql db copy -g mygroup -s myserver -n originalDb --dest-name newDb --service-objective S0
        - name: Create a database with GeneralPurpose edition, Gen4 hardware, and 1 vcore as a copy of an existing GeneralPurpose database.
          text: az sql db copy -g mygroup -s myserver -n originalDb --dest-name newDb -f Gen4 -c 1
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
    """
helps['sql db delete'] = """
    type: command
    short-summary: Delete a database.
    """
helps['sql db list'] = """
    type: command
    short-summary: List databases a server or elastic pool.
    """
helps['sql db list-editions'] = """
    type: command
    short-summary: Show database editions available for the currently active subscription.
    long-summary: Includes available service objectives and storage limits. In order to reduce verbosity, settings to intentionally reduce storage limits are hidden by default.
    examples:
        - name: Show all database editions in a location.
          text: az sql db list-editions -l westus
        - name: Show all available database service objectives for Standard edition.
          text: az sql db list-editions -l westus --edition Standard
        - name: Show available max database sizes for P1 service objective
          text: az sql db list-editions -l westus --service-objective P1 --show-details max-size
    """
helps['sql db rename'] = """
    type: command
    short-summary: Rename a database.
    """
helps['sql db show'] = """
    type: command
    short-summary: Get the details for a database.
    """
helps['sql db show-connection-string'] = """
    type: command
    short-summary: Generates a connection string to a database.
    examples:
        - name: Generate connection string for ado.net
          text: az sql db show-connection-string -s myserver -n mydb -c ado.net
    """
helps['sql db update'] = """
    type: command
    short-summary: Update a database.
    examples:
        - name: Update database with zone redundancy enabled
          text: az sql db update -g mygroup -s myserver -n mypool -z
        - name: Update database with zone redundancy explicitly disabled
          text: az sql db update -g mygroup -s myserver -n mypool -z false
    """
helps['sql db audit-policy'] = """
    type: group
    short-summary: Manage a database's auditing policy.
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
helps['sql db audit-policy update'] = """
    type: command
    short-summary: Update a database's auditing policy.
    long-summary: If the policy is being enabled, `--storage-account` or both `--storage-endpoint` and `--storage-key` must be specified.
    examples:
        - name: Enable by storage account name.
          text: az sql db audit-policy update -g mygroup -s myserver -n mydb --state Enabled --storage-account mystorage
        - name: Enable by storage endpoint and key.
          text: |
            az sql db audit-policy update -g mygroup -s myserver -n mydb --state Enabled \\
                --storage-endpoint https://mystorage.blob.core.windows.net --storage-key MYKEY==
        - name: Set the list of audit actions.
          text: |
            az sql db audit-policy update -g mygroup -s myserver -n mydb \\
                --actions FAILED_DATABASE_AUTHENTICATION_GROUP 'UPDATE on database::mydb by public'
        - name: Add an audit action.
          text: |
            az sql db audit-policy update -g mygroup -s myserver -n mydb \\
                --add auditActionsAndGroups FAILED_DATABASE_AUTHENTICATION_GROUP
        - name: Remove an audit action by list index.
          text: az sql db audit-policy update -g mygroup -s myserver -n mydb --remove auditActionsAndGroups 0
        - name: Disable an auditing policy.
          text: az sql db audit-policy update -g mygroup -s myserver -n mydb --state Disabled
    """
helps['sql db op'] = """
    type: group
    short-summary: Manage operations on a database.
    """
helps['sql db op cancel'] = """
    type: command
    examples:
        - name: Cancel an operation.
          text: az sql db op cancel -g mygroup -s myserver -d mydb -n d2896db1-2ba8-4c84-bac1-387c430cce40
    """
helps['sql db replica'] = """
    type: group
    short-summary: Manage replication between databases.
    """
helps['sql db replica create'] = """
    type: command
    short-summary: Create a database as a readable secondary replica of an existing database.
    long-summary: A full list of performance level options can be seen by executing `az sql db list-editions -a -o table -l LOCATION`.
                  The secondary database must have the same edition as the primary database.
    examples:
        - name: Create a database with performance level S0 as a secondary replica of an existing Standard database.
          text: az sql db replica create -g mygroup -s myserver -n originalDb --partner-server newDb --service-objective S0
        - name: Create a database with GeneralPurpose edition, Gen4 hardware, and 1 vcore as a secondary replica of an existing GeneralPurpose database
          text: az sql db replica create -g mygroup -s myserver -n originalDb --partner-server newDb -f Gen4 -c 1
    """
helps['sql db replica set-primary'] = """
    type: command
    short-summary: Set the primary replica database by failing over from the current primary replica database.
    """
helps['sql db replica list-links'] = """
    type: command
    short-summary: List the replicas of a database and their replication status.
    """
helps['sql db replica delete-link'] = """
    type: command
    short-summary: Permanently stop data replication between two database replicas.
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
                --storage-uri https://mystorageaccount.blob.core.windows.net/bacpacs/myBacpac.bacpac
        - name: Export bacpac using a storage account key.
          text: |
            az sql db export -s myserver -n mydatabase -g mygroup -p password -u login \\
                --storage-key MYKEY== --storage-key-type StorageAccessKey \\
                --storage-uri https://mystorageaccount.blob.core.windows.net/bacpacs/myBacpac.bacpac
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
                --storage-uri https://mystorageaccount.blob.core.windows.net/bacpacs/myBacpac.bacpac
        - name: Import bacpac into an existing database using a storage account key.
          text: |
            az sql db import -s myserver -n mydatabase -g mygroup -p password -u login --storage-key MYKEY== \\
                --storage-key-type StorageAccessKey \\
                --storage-uri https://mystorageaccount.blob.core.windows.net/bacpacs/myBacpac.bacpac
    """
helps['sql db restore'] = """
    type: command
    short-summary: Create a new database by restoring from a backup.
    """
helps['sql db threat-policy'] = """
    type: group
    short-summary: Manage a database's threat detection policies.
    """
helps['sql db threat-policy update'] = """
    type: command
    short-summary: Update a database's threat detection policy.
    long-summary: If the policy is being enabled, storage_account or both storage_endpoint and
                  storage_account_access_key must be specified.
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
helps['sql db tde'] = """
            type: group
            short-summary: Manage a database's transparent data encryption.
            """
helps['sql db tde set'] = """
            type: command
            short-summary: Sets a database's transparent data encryption configuration.
            """
helps['sql dw'] = """
    type: group
    short-summary: Manage data warehouses.
    """
helps['sql dw create'] = """
    type: command
    short-summary: Create a data warehouse.
    """
helps['sql dw delete'] = """
    type: command
    short-summary: Delete a data warehouse.
    """
helps['sql dw list'] = """
    type: command
    short-summary: List data warehouses for a server.
    """
helps['sql dw show'] = """
    type: command
    short-summary: Get the details for a data warehouse.
    """
helps['sql dw update'] = """
    type: command
    short-summary: Update a data warehouse.
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
    """
helps['sql elastic-pool list-editions'] = """
    type: command
    short-summary: List elastic pool editions available for the active subscription.
    long-summary: Also includes available pool DTU settings, storage limits, and per database
                  settings. In order to reduce verbosity, additional storage limits and per
                  database settings are hidden by default.
    examples:
        - name: Show all elastic pool editions and pool DTU limits in the West US region.
          text: az sql elastic-pool list-editions -l westus
        - name: Show all pool DTU limits for Standard edition in the West US region.
          text: az sql elastic-pool list-editions -l westus --edition Standard
        - name: Show available max sizes for elastic pools with at least 100 DTUs in the West US region.
          text: az sql elastic-pool list-editions -l westus --dtu 100 --show-details max-size
        - name: Show available per database settings for Standard 100 DTU elastic pools in the West US region.
          text: az sql elastic-pool list-editions -l westus --edition Standard --dtu 100
                --show-details db-min-dtu db-max-dtu db-max-size
    """
helps['sql elastic-pool update'] = """
    type: command
    short-summary: Update an elastic pool.
    examples:
        - name: Update elastic pool with zone redundancy enabled
          text: az sql elastic-pool update -g mygroup -s myserver -n mypool -z
        - name: Update elastic pool with zone redundancy explicitly disabled
          text: az sql elastic-pool update -g mygroup -s myserver -n mypool -z false
    """
helps['sql elastic-pool op'] = """
    type: group
    short-summary: Manage operations on an elastic pool.
    """
helps['sql elastic-pool op cancel'] = """
    type: command
    examples:
        - name: Cancel an operation.
          text: az sql elastic-pool op cancel -g mygroup -s myserver -ep myelasticpool -n d2896db1-2ba8-4c84-bac1-387c430cce40
    """
helps['sql failover-group'] = """
    type: group
    short-summary: Manage SQL Failover Groups.
    """
helps['sql failover-group create'] = """
    type: command
    short-summary: Creates a failover group.
    """
helps['sql failover-group update'] = """
    type: command
    short-summary: Updates the failover group.
    """
helps['sql failover-group set-primary'] = """
    type: command
    short-summary: Set the primary of the failover group by failing over all databases from the current primary server.
    """
helps['sql server'] = """
    type: group
    short-summary: Manage SQL servers.
    """
helps['sql server create'] = """
    type: command
    short-summary: Create a server.
    examples:
        - name: Create a server.
          text: az sql server create -l westus -g mygroup -n myserver -u myadminuser -p myadminpassword
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
helps['sql server update'] = """
    type: command
    short-summary: Update a server.
    """
helps['sql server conn-policy'] = """
    type: group
    short-summary: Manage a server's connection policy.
    """
helps['sql server conn-policy show'] = """
    type: command
    short-summary: Gets a server's secure connection policy.
    """
helps['sql server conn-policy update'] = """
    type: command
    short-summary: Updates a server's secure connection policy.
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
          text: az sql server firewall-rule create -g mygroup -s myserver -n myrule
                --start-ip-address 1.2.3.4 --end-ip-address 5.6.7.8
        - name: Create a firewall rule that allows access from Azure services
          text: az sql server firewall-rule create -g mygroup -s myserver -n myrule
                --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
    """
helps['sql server firewall-rule update'] = """
    type: command
    short-summary: Update a firewall rule.
    examples:
        - name: Update a firewall rule
          text: az sql server firewall-rule update -g mygroup -s myserver -n myrule
                --start-ip-address 9.8.7.6 --end-ip-address 5.4.3.2
    """
helps['sql server firewall-rule show'] = """
    type: command
    short-summary: Shows the details for a firewall rule.
    examples:
        - name: Show a firewall rule
          text: az sql server firewall-rule show -g mygroup -s myserver -n myrule
    """
helps['sql server firewall-rule list'] = """
    type: command
    short-summary: List a server's firewall rules.
    examples:
        - name: List a server's firewall rules
          text: az sql server firewall-rule list -g mygroup -s myserver
    """
helps['sql server key'] = """
    type: group
    short-summary: Manage a server's keys.
    """
helps['sql server key create'] = """
    type: command
    short-summary: Creates a server key.
    """
helps['sql server key show'] = """
    type: command
    short-summary: Shows a server key.
    """
helps['sql server key delete'] = """
    type: command
    short-summary: Deletes a server key.
    """
helps['sql server tde-key'] = """
    type: group
    short-summary: Manage a server's encryption protector.
    """
helps['sql server tde-key set'] = """
    type: command
    short-summary: Sets the server's encryption protector.
    """
helps['sql server vnet-rule'] = """
    type: group
    short-summary: Manage a server's virtual network rules.
    """
helps['sql server vnet-rule update'] = """
    type: command
    short-summary: Update a virtual network rule.
    """
helps['sql server vnet-rule create'] = """
    type: command
    short-summary: Create a virtual network rule to allows access to an Azure SQL server.

    examples:
        - name: Create a vnet rule by providing the subnet id.
          text: |
            az sql server vnet-rule create \\
              --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName}
        - name: Create a vnet rule by providing the vnet and subnet name. The subnet id is created by taking the resource group name and subscription id of the SQL server.
          text: az sql server vnet-rule create --subnet subnetName --vnet-name vnetName
    """
helps['sql mi'] = """
    type: group
    short-summary: Manage SQL managed instances.
    """
helps['sql mi create'] = """
    type: command
    short-summary: Create a managed instance.
    examples:
        - name: Create a managed instance with specified parameters and with identity
          text: az sql mi create -g mygroup -n myinstance -l mylocation -i -u myusername -p mypassword --license-type LicenseIncluded --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName} --capacity 8 --storage 32GB --edition GeneralPurpose --family Gen4
        - name: Create a managed instance with minimal set of parameters
          text: az sql mi create -g mygroup -n myinstance -l mylocation -i -u myusername -p mypassword --subnet /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}/subnets/{SubnetName}
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
helps['sql mi show'] = """
    type: command
    short-summary: Get the details for a managed instance.
    examples:
        - name: Get the details for a managed instance
          text: az sql mi show -g mygroup -n myinstance
    """
helps['sql mi update'] = """
    type: command
    short-summary: Update a managed instance.
    examples:
        - name: Updates a mi with specified parameters and with identity
          text: az sql mi update -g mygroup -n myinstance -i -p mypassword --license-type mylicensetype --capacity vcorecapacity --storage storagesize
    """
helps['sql mi delete'] = """
    type: command
    short-summary: Delete a managed instance.
    examples:
        - name: Delete a managed instance
          text: az sql mi delete -g mygroup -n myinstance --yes
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
helps['sql midb list'] = """
    type: command
    short-summary: List maanged databases on a managed instance.
    examples:
        - name: List managed databases on a managed instance
          text: az sql midb list -g mygroup --mi myinstance
    """
helps['sql midb show'] = """
    type: command
    short-summary: Get the details for a managed database.
    examples:
        - name: Get the details for a managed database
          text: az sql midb show -g mygroup --mi myinstance -n mymanageddb
    """
helps['sql midb restore'] = """
    type: command
    short-summary: Restore a managed database.
    examples:
        - name: Restore a managed database using Point in time restore
          text: az sql midb restore -g mygroup --mi myinstance -n mymanageddb --dest-name targetmidb --time "2018-05-20T05:34:22"
    """
helps['sql midb delete'] = """
    type: command
    short-summary: Delete a managed database.
    examples:
        - name: Delete a managed database
          text: az sql midb delete -g mygroup --mi myinstance -n mymanageddb --yes
    """
