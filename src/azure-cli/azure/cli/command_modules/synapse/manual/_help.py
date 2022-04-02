# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-lines

from knack.help_files import helps


helps['synapse'] = """
type: group
short-summary: Manage and operate Synapse Workspace, Spark Pool, SQL Pool.
"""

helps['synapse workspace'] = """
type: group
short-summary: Manage Synapse workspaces.
"""

helps['synapse workspace create'] = """
type: command
short-summary: Create a Synapse workspace.
examples:
  - name: Create a Synapse workspace
    text: |-
        az synapse workspace create --name testworkspace --resource-group rg \\
          --storage-account testadlsgen2 --file-system testfilesystem \\
          --sql-admin-login-user cliuser1 --sql-admin-login-password Password123! --location "East US"
  - name: Create a Synapse workspace with storage resource id
    text: |-
        az synapse workspace create --name testworkspace --resource-group rg \\
          --storage-account /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/testadlsgen2 --file-system testfilesystem \\
          --sql-admin-login-user cliuser1 --sql-admin-login-password Password123! --location "East US"
  - name: Create a Synapse workspace using customer-managed key
    text: |-
        az synapse workspace create --name testworkspace --resource-group rg \\
          --storage-account testadlsgen2 --file-system testfilesystem \\
          --sql-admin-login-user cliuser1 --sql-admin-login-password Password123! --location "East US" \\
          --key-identifier https://{keyvaultname}.vault.azure.net/keys/{keyname} --key-name testcmk
  - name: Create a Synapse workspace connecting to azure devops
    text: |-
        az synapse workspace create --name testworkspace --resource-group rg \\
          --storage-account testadlsgen2 --file-system testfilesystem \\
          --sql-admin-login-user cliuser1 --sql-admin-login-password Password123! --location "East US" \\
          --repository-type AzureDevOpsGit --account-name testuser --project-name testprj \\
          --repository-name testrepo --collaboration-branch main
"""

helps['synapse workspace list'] = """
type: command
short-summary: List all Synapse workspaces.
examples:
  - name: List all Synapse workspaces under a subscription
    text: |-
        az synapse workspace list
  - name: List all Synapse workspaces under a specific resource group
    text: |-
        az synapse workspace list --resource-group rg
"""

helps['synapse workspace show'] = """
type: command
short-summary: Get a Synapse workspace.
examples:
  - name: Get a Synapse workspace.
    text: |-
        az synapse workspace show --name testsynapseworkspace --resource-group rg
"""

helps['synapse workspace update'] = """
type: command
short-summary: Update a Synapse workspace.
examples:
  - name: Update a Synapse workspace
    text: |-
        az synapse workspace update --name fromcli4 --resource-group rg \\
          --tags key1=value1
"""

helps['synapse workspace delete'] = """
type: command
short-summary: Delete a Synapse workspace.
examples:
  - name: Delete a Synapse workspace.
    text: |-
        az synapse workspace delete --name testsynapseworkspace --resource-group rg
"""

helps['synapse workspace check-name'] = """
type: command
short-summary: Check if a Synapse workspace name is available or not.
examples:
  - name: Check if a Synapse workspace name is available or not.
    text: |-
        az synapse workspace check-name --name testsynapseworkspace
"""

helps['synapse workspace wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the workspace is met.
"""

helps['synapse spark'] = """
type: group
short-summary: Manage Spark pools and Spark jobs.
"""

helps['synapse spark pool'] = """
type: group
short-summary: Manage Spark pools.
"""

helps['synapse spark pool create'] = """
type: command
short-summary: Create a Spark pool.
examples:
  - name: Create a Spark pool.
    text: |-
        az synapse spark pool create --name testpool --workspace-name testsynapseworkspace --resource-group rg \\
        --spark-version 2.4 --node-count 3 --node-size Medium --spark-config-file-path 'path/configfile.txt'
"""

helps['synapse spark pool list'] = """
type: command
short-summary: List all Spark pools.
examples:
  - name: List all Spark pools.
    text: |-
        az synapse spark pool list --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse spark pool show'] = """
type: command
short-summary: Get a Spark pool.
examples:
  - name: Get a Spark pool.
    text: |-
        az synapse spark pool show --name testpool --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse spark pool update'] = """
type: command
short-summary: Update the Spark pool.
examples:
  - name: Update the Spark pool's tags.
    text: |-
        az synapse spark pool update --name testpool --workspace-name testsynapseworkspace --resource-group rg \\
        --tags key1=value1
  - name: Update the Spark pool's auto scale configuration.
    text: |-
        az synapse spark pool update --name testpool --workspace-name testsynapseworkspace --resource-group rg \\
        --enable-auto-scale --min-node-count 3 --max-node-count 100
  - name: Update the Spark pool's custom libraries.
    text: |-
        az synapse spark pool update --name testpool --workspace-name testsynapseworkspace --resource-group rg \\
        --package-action Add --package package1.jar package2.jar
  - name: Update the Spark pool's configuration file.
    text: |-
        az synapse spark pool update --name testpool --workspace-name testsynapseworkspace --resource-group rg \\
        --spark-config-file-path 'path/configfile.txt'
"""

helps['synapse spark pool delete'] = """
type: command
short-summary: Delete a Spark pool.
examples:
  - name: Delete a Spark pool.
    text: |-
        az synapse spark pool delete --name testpool --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse spark pool wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a Spark pool is met.
"""

helps['synapse sql'] = """
type: group
short-summary: Manage SQL pools.
"""

helps['synapse sql ad-admin'] = """
type: group
short-summary: Manage SQL Active Directory administrator.
"""

helps['synapse sql ad-admin show'] = """
type: command
short-summary: Get the SQL Azure Active Directory administrator.
examples:
  - name: Get the SQL Azure Active admin.
    text: |-
        az synapse sql ad-admin show --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql ad-admin create'] = """
type: command
short-summary: Create the SQL Azure Active Directory administrator.
examples:
  - name: Create the SQL Azure Active admin.
    text: |-
        az synapse sql ad-admin create --workspace-name testsynapseworkspace --resource-group rg \\
        --display-name youraccount@yourdomain --object-id 00000000-0000-0000-0000-000000000000
"""

helps['synapse sql ad-admin update'] = """
type: command
short-summary: Update the SQL Azure Active Directory administrator.
examples:
  - name: Update the SQL Azure Active admin.
    text: |-
        az synapse sql ad-admin update --workspace-name testsynapseworkspace --resource-group rg \\
        --display-name youraccount@yourdomain --object-id 00000000-0000-0000-0000-000000000000
"""

helps['synapse sql ad-admin delete'] = """
type: command
short-summary: Delete the SQL Azure Active Directory administrator.
examples:
  - name: Delete the SQL Azure Active admin.
    text: |-
        az synapse sql ad-admin delete --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql ad-admin wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition is met.
"""

helps['synapse sql audit-policy'] = """
type: group
short-summary: Manage SQL auditing policy.
"""

helps['synapse sql audit-policy show'] = """
type: command
short-summary: Get a SQL's auditing policy.
examples:
  - name: Get a SQL's auditing policy.
    text: |-
        az synapse sql audit-policy show --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql audit-policy update'] = """
type: command
short-summary: Update a SQL's auditing policy.
long-summary: If the policy is being enabled, `--storage-account` or both `--storage-endpoint` and `--storage-key` must be specified.
examples:
  - name: Enable by storage account name.
    text: |
        az synapse sql audit-policy update --workspace-name testsynapseworkspace --resource-group rg --state Enabled \\
            --blob-storage-target-state Enabled --storage-account mystorage
  - name: Enable by storage endpoint and key.
    text: |
        az synapse sql audit-policy update --workspace-name testsynapseworkspace --resource-group rg --state Enabled \\
            --blob-storage-target-state Enabled --storage-endpoint https://mystorage.blob.core.windows.net \\
            --storage-key MYKEY==
  - name: Set the list of audit actions.
    text: |
        az synapse sql audit-policy update --workspace-name testsynapseworkspace --resource-group rg \\
        --actions SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP 'UPDATE on database::mydb by public'
  - name: Disable an auditing policy.
    text: |-
        az synapse sql audit-policy update --workspace-name testsynapseworkspace --resource-group rg \\
        --state Disabled
  - name: Disable a blob storage auditing policy.
    text: |-
        az synapse sql audit-policy update --workspace-name testsynapseworkspace --resource-group rg \\
        --blob-storage-target-state Disabled
  - name: Enable a log analytics auditing policy.
    text: |
        az synapse sql audit-policy update --resource-group mygroup --workspace-name myws --state Enabled \\
            --log-analytics-target-state Enabled --log-analytics-workspace-resource-id myworkspaceresourceid
  - name: Disable a log analytics auditing policy.
    text: |
        az synapse sql audit-policy update --resource-group mygroup --workspace-name myws --state Enabled
            --log-analytics-target-state Disabled
  - name: Enable an event hub auditing policy.
    text: |
        az synapse sql audit-policy update --resource-group mygroup --workspace-name myws --state Enabled \\
            --event-hub-target-state Enabled \\
            --event-hub-authorization-rule-id eventhubauthorizationruleid \\
            --event-hub eventhubname
  - name: Enable an event hub auditing policy for default event hub.
    text: |
        az synapse sql audit-policy update --resource-group mygroup --workspace-name myws --state Enabled \\
            --event-hub-target-state Enabled \\
            --event-hub-authorization-rule-id eventhubauthorizationruleid
  - name: Disable an event hub auditing policy.
    text: |
        az synapse sql audit-policy update --resource-group mygroup --workspace-name myws
           --state Enabled --event-hub-target-state Disabled
"""

helps['synapse sql audit-policy wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition is met.
"""

helps['synapse sql pool'] = """
type: group
short-summary: Manage SQL pools.
"""

helps['synapse sql pool create'] = """
type: command
short-summary: Create a SQL pool.
examples:
  - name: Create a SQL pool.
    text: |-
        az synapse sql pool create --name sqlpool --performance-level "DW1000c" \\
        --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool show'] = """
type: command
short-summary: Get a SQL pool.
examples:
  - name: Get a SQL pool.
    text: |-
        az synapse sql pool show --name sqlpool --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool list'] = """
type: command
short-summary: List all SQL pools.
examples:
  - name: List SQL pools.
    text: |-
        az synapse sql pool list --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool update'] = """
type: command
short-summary: Update a SQL pool.
examples:
  - name: Update a SQL pool.
    text: |-
        az synapse sql pool update --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --tags key1=value1
"""

helps['synapse sql pool pause'] = """
type: command
short-summary: Pause a SQL pool.
examples:
  - name: Pause a SQL pool.
    text: |-
        az synapse sql pool pause --name sqlpool --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool resume'] = """
type: command
short-summary: Resume a SQL pool.
examples:
  - name: Resume a SQL pool.
    text: |-
        az synapse sql pool resume --name sqlpool --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool delete'] = """
type: command
short-summary: Delete a SQL pool.
examples:
  - name: Delete a SQL pool.
    text: |-
        az synapse sql pool delete --name sqlpool --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool restore'] = """
type: command
short-summary: Create a new SQL pool by restoring from a backup.
examples:
  - name: Create a new SQL pool by restoring an existing SQL pool's restore point.
    text: |-
        az synapse sql pool restore --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --dest-name newsqlpool --time 2020-11-25T02:47:37
"""

helps['synapse sql pool show-connection-string'] = """
type: command
short-summary: Generate a connection string to a SQL pool.
examples:
  - name: Generate connection string for ado.net
    text: |-
        az synapse sql pool show-connection-string --name sqlpool --workspace-name testsynapseworkspace -c ado.net
"""

helps['synapse sql pool list-deleted'] = """
type: command
short-summary: List all deleted SQL pools.
examples:
  - name: List deleted SQL pools.
    text: |-
        az synapse sql pool list-deleted --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a SQL pool is met.
"""

helps['synapse sql pool classification'] = """
type: group
short-summary: Manage sensitivity classifications.
"""

helps['synapse sql pool classification create'] = """
type: command
short-summary: Create a column's sensitivity classification.
examples:
  - name: Create sensitivity classification for a given column.
    text: |-
        az synapse sql pool classification create --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --schema dbo --table mytable --column mycolumn \\
        --information-type Name --label "Confidential - GDPR"
"""

helps['synapse sql pool classification update'] = """
type: command
short-summary: Update a column's sensitivity classification.
examples:
  - name: Update sensitivity classification for a given column.
    text: |-
        az synapse sql pool classification update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --schema dbo --table mytable --column mycolumn \\
        --information-type Name --label "Confidential - GDPR"
"""

helps['synapse sql pool classification list'] = """
type: command
short-summary: Get the sensitivity classifications of a given SQL pool.
examples:
  - name: List the sensitivity classification of a given SQL pool.
    text: |-
        az synapse sql pool classification list --name sqlpool --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool classification show'] = """
type: command
short-summary: Get the sensitivity classification of a given column.
examples:
  - name: Get the sensitivity classification of a given column.
    text: |-
        az synapse sql pool classification show --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --schema dbo --table mytable --column mycolumn
"""

helps['synapse sql pool classification delete'] = """
type: command
short-summary: Delete the sensitivity classification of a given column.
examples:
  - name: Delete the sensitivity classification of a given column.
    text: |-
        az synapse sql pool classification delete --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --schema dbo --table mytable --column mycolumn
"""

helps['synapse sql pool classification recommendation'] = """
type: group
short-summary: Manage sensitivity classification recommendations.
"""

helps['synapse sql pool classification recommendation list'] = """
type: command
short-summary: List the recommended sensitivity classifications of a given SQL pool.
examples:
  - name: List the recommended sensitivity classifications of a given SQL pool.
    text: |-
        az synapse sql pool classification recommendation list --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg
"""

helps['synapse sql pool classification recommendation enable'] = """
type: command
short-summary: Enable sensitivity recommendations for a given column(recommendations are enabled by default on all columns).
examples:
  - name: Enable sensitivity recommendations for a given column.
    text: |-
        az synapse sql pool classification recommendation enable --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --schema dbo --table mytable --column mycolumn
"""

helps['synapse sql pool classification recommendation disable'] = """
type: command
short-summary: Disable sensitivity recommendations for a given column(recommendations are enabled by default on all columns).
examples:
  - name: Disable sensitivity recommendations for a given column.
    text: |-
        az synapse sql pool classification recommendation disable --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --schema dbo --table mytable --column mycolumn
"""

helps['synapse sql pool tde'] = """
type: group
short-summary: Manage a SQL pool's transparent data encryption.
"""

helps['synapse sql pool tde set'] = """
type: command
short-summary: Set a SQL pool's transparent data encryption configuration.
examples:
  - name: Set a SQL pool's transparent data encryption configuration. (autogenerated)
    text: |-
        az synapse sql pool tde set --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --status Enabled --transparent-data-encryption-name tdename
"""

helps['synapse sql pool tde show'] = """
type: command
short-summary: Get a SQL pool's transparent data encryption configuration.
examples:
  - name: Get a SQL pool's transparent data encryption configuration. (autogenerated)
    text: |-
        az synapse sql pool tde show --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --transparent-data-encryption-name tdename
"""

helps['synapse sql pool threat-policy'] = """
type: group
short-summary: Manage a SQL pool's threat detection policies.
"""

helps['synapse sql pool threat-policy show'] = """
type: command
short-summary: Get a SQL pool's threat detection policy.
examples:
  - name: Get a SQL pool's threat detection policy.
    text: |-
        az synapse sql pool threat-policy show --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --security-alert-policy-name threatpolicy
"""

helps['synapse sql pool threat-policy update'] = """
type: command
short-summary: Update a SQL pool's threat detection policy.
long-summary: If the policy is being enabled, storage_account or both storage_endpoint and storage_account_access_key must be specified.
examples:
  - name: Enable by storage account name.
    text: |-
        az synapse sql pool threat-policy update --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --state Enabled --storage-account mystorageaccount --security-alert-policy-name threatpolicy
  - name: Enable by storage endpoint and key.
    text: |-
        az synapse sql pool threat-policy update --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --state Enabled --storage-endpoint https://mystorage.blob.core.windows.net --storage-key MYKEY== \\
        --security-alert-policy-name threatpolicy
  - name: Disable a subset of alert types.
    text: |-
        az synapse sql pool threat-policy update --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --disabled-alerts Sql_Injection_Vulnerability Access_Anomaly --security-alert-policy-name threatpolicy
  - name: Configure email recipients for a policy.
    text: |-
        az synapse sql pool threat-policy update --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --email-addresses me@examlee.com you@example.com --email-account-admins true \\
        --security-alert-policy-name threatpolicy
  - name: Disable a threat policy.
    text: |-
        az synapse sql pool threat-policy update --name sqlpool --workspace-name testsynapseworkspace --resource-group rg \\
        --state Disabled --security-alert-policy-name threatpolicy
"""

helps['synapse sql pool audit-policy'] = """
type: group
short-summary: Manage a SQL pool's auditing policy.
"""

helps['synapse sql pool audit-policy show'] = """
type: command
short-summary: Get a SQL pool's auditing policy.
examples:
  - name: Get a SQL pool's auditing policy.
    text: |-
        az synapse sql pool audit-policy show --name sqlpool --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool audit-policy update'] = """
type: command
short-summary: Update a SQL pool's auditing policy.
long-summary: If the policy is being enabled, `--storage-account` or both `--storage-endpoint` and `--storage-key` must be specified.
examples:
  - name: Enable by storage account name.
    text: |
        az synapse sql pool audit-policy update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --state Enabled --blob-storage-target-state Enabled --storage-account mystorage
  - name: Enable by storage endpoint and key.
    text: |
        az synapse sql pool audit-policy update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --state Enabled --blob-storage-target-state Enabled \\
        --storage-endpoint https://mystorage.blob.core.windows.net --storage-key MYKEY==
  - name: Set the list of audit actions.
    text: |
        az synapse sql pool audit-policy update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --actions SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP 'UPDATE on database::mydb by public'
  - name: Disable an auditing policy.
    text: |-
        az synapse sql pool audit-policy update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --state Disabled
  - name: Disable a blob storage auditing policy.
    text: |-
        az synapse sql pool audit-policy update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --blob-storage-target-state Disabled
  - name: Enable a log analytics auditing policy.
    text: |
        az synapse sql pool audit-policy update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --state Enabled --log-analytics-target-state Enabled \\
        --log-analytics-workspace-resource-id myworkspaceresourceid
  - name: Disable a log analytics auditing policy.
    text: |
        az synapse sql pool audit-policy update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --log-analytics-target-state Disabled
  - name: Enable an event hub auditing policy.
    text: |
        az synapse sql pool audit-policy update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --state Enabled --event-hub-target-state Enabled \\
        --event-hub-authorization-rule-id eventhubauthorizationruleid --event-hub eventhubname
  - name: Enable an event hub auditing policy for default event hub.
    text: |
        az synapse sql pool audit-policy update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg --state Enabled --event-hub-target-state Enabled \\
        --event-hub-authorization-rule-id eventhubauthorizationruleid
  - name: Disable an event hub auditing policy.
    text: |
        az synapse sql pool audit-policy update --name sqlpool --workspace-name testsynapseworkspace \\
        --resource-group rg  --event-hub-target-state Disabled
"""

helps['synapse workspace key'] = """
type: group
short-summary:  Manage workspace's keys.
"""

helps['synapse workspace key create'] = """
type: command
short-summary: Create a workspace's key.
examples:
  - name: Create a workspace's key.
    text: |-
        az synapse workspace key create --name newkey --workspace-name testsynapseworkspace \\
        --resource-group rg --key-identifier https://{keyvaultname}.vault.azure.net/keys/{keyname}
"""

helps['synapse workspace activate'] = """
type: command
short-summary: Activates a workspace and change it's state from pending to success state when the workspace is first being provisioned and double encryption is enabled.
long-summary: When creating an Azure Synapse Analytics workspace, you can choose to encrypt all data at rest in the workspace with a customer-managed key which will provide double encryption to the workspace.You may need to set up the encryption environment firstly, such as to create a key vault with purge protection enable and specify Access Polices to the key vault. Then use this cmdlet to activate the new Azure Synapse Analytics workspace which double encryption is enabled using a customer-managed key.
examples:
  - name: activate a workspace.
    text: |-
        az synapse workspace activate --name newkey --workspace-name testsynapseworkspace \\
        --resource-group rg --key-identifier https://{keyvaultname}.vault.azure.net/keys/{keyname}
"""

helps['synapse workspace key delete'] = """
type: command
short-summary: Delete a workspace's key. The key at active status can't be deleted.
examples:
  - name: Delete a workspace's key.
    text: |-
        az synapse workspace key delete --name newkey --workspace-name testsynapseworkspace \\
        --resource-group rg
"""

helps['synapse workspace key show'] = """
type: command
short-summary: Show a workspace's key by name.
examples:
  - name: Show a workspace's key.
    text: |-
        az synapse workspace key show --name newkey --workspace-name testsynapseworkspace \\
        --resource-group rg
"""

helps['synapse workspace key list'] = """
type: command
short-summary: List keys under specified workspace.
examples:
  - name: List keys under specified workspace.
    text: |-
        az synapse workspace key list --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse workspace key wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a workspace key is met.
"""

helps['synapse workspace managed-identity'] = """
type: group
short-summary:  Manage workspace's managed-identity.
"""

helps['synapse workspace managed-identity show-sql-access'] = """
type: command
short-summary: Show workspace's sql-access state to managed-identity.
examples:
  - name: Show workspace's sql-access state to managed-identity.
    text: |-
        az synapse workspace managed-identity show-sql-access --workspace-name testsynapseworkspace \\
        --resource-group rg
"""

helps['synapse workspace managed-identity revoke-sql-access'] = """
type: command
short-summary: Revoke workspace's sql-access to managed-identity.
examples:
  - name: Revoke workspace's sql-access to managed-identity.
    text: |-
        az synapse workspace managed-identity revoke-sql-access --workspace-name testsynapseworkspace \\
        --resource-group rg
"""

helps['synapse workspace managed-identity grant-sql-access'] = """
type: command
short-summary: Grant workspace's sql-access to managed-identity.
examples:
  - name: Grant workspace's sql-access to managed-identity.
    text: |-
        az synapse workspace managed-identity grant-sql-access --workspace-name testsynapseworkspace \\
        --resource-group rg
"""

helps['synapse workspace managed-identity wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of sql-access state to managed-identity is met.
"""

helps['synapse workspace firewall-rule'] = """
type: group
short-summary:  Manage a workspace's firewall rules.
"""

helps['synapse workspace firewall-rule create'] = """
type: command
short-summary: Create a firewall rule.
examples:
  - name: Create a firewall rule.
    text: |-
        az synapse workspace firewall-rule create --name allowAll --workspace-name testsynapseworkspace \\
        --resource-group rg --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255
"""

helps['synapse workspace firewall-rule update'] = """
type: command
short-summary: Update a firewall rule.
examples:
  - name: Update a firewall rule.
    text: |-
        az synapse workspace firewall-rule update --name allowAll --workspace-name testsynapseworkspace \\
        --resource-group rg --start-ip-address 172.0.0.0
"""

helps['synapse workspace firewall-rule show'] = """
type: command
short-summary: Get a firewall rule.
examples:
  - name: Get a firewall rule.
    text: |-
        az synapse workspace firewall-rule show --name rule1 --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse workspace firewall-rule list'] = """
type: command
short-summary: List all firewall rules.
examples:
  - name: List all firewall rules.
    text: |-
        az synapse workspace firewall-rule list --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse workspace firewall-rule delete'] = """
type: command
short-summary: Delete a firewall rule.
examples:
  - name: Delete a firewall rule.
    text: |-
        az synapse workspace firewall-rule delete --name rule1 --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse workspace firewall-rule wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a firewall rule is met.
"""

helps['synapse spark job'] = """
type: group
short-summary: Manage Synapse Spark batch jobs.
"""

helps['synapse spark job submit'] = """
type: command
short-summary: Submit a Spark job.
examples:
  - name: Submit a Java Spark job.
    text: |-
        az synapse spark job submit --name WordCount_Java --workspace-name testsynapseworkspace \\
        --spark-pool-name testsparkpool \\
        --main-definition-file abfss://testfilesystem@testadlsgen2.dfs.core.windows.net/samples/java/wordcount/wordcount.jar \\
        --main-class-name WordCount \\
        --arguments abfss://testfilesystem@testadlsgen2.dfs.core.windows.net/samples/java/wordcount/shakespeare.txt \\
        abfss://testfilesystem@testadlsgen2.dfs.core.windows.net/samples/java/wordcount/result/ \\
        --executors 2 --executor-size Small
"""

helps['synapse spark job list'] = """
type: command
short-summary: List all Spark jobs.
examples:
  - name: List all Spark jobs.
    text: |-
        az synapse spark job list --workspace-name testsynapseworkspace --spark-pool-name testsparkpool
"""

helps['synapse spark job show'] = """
type: command
short-summary: Get a Spark job.
examples:
  - name: Get a Spark job.
    text: |-
        az synapse spark job show --livy-id 1 --workspace-name testsynapseworkspace --spark-pool-name testsparkpool
"""

helps['synapse spark job cancel'] = """
type: command
short-summary: Cancel a Spark job.
examples:
  - name: Cancel a Spark job.
    text: |-
        az synapse spark job cancel --livy-id 1 --workspace-name testsynapseworkspace --spark-pool-name testsparkpool
"""

helps['synapse spark session'] = """
type: group
short-summary: Manage Synapse Spark sessions.
"""

helps['synapse spark session create'] = """
type: command
short-summary: Create a Spark session.
examples:
  - name: Create a Spark session.
    text: |-
        az synapse spark session create --name testsession  --workspace-name testsynapseworkspace \\
        --spark-pool-name testsparkpool --executor-size Small --executors 4
"""

helps['synapse spark session list'] = """
type: command
short-summary: List all Spark sessions.
examples:
  - name: List all Spark sessions.
    text: |-
        az synapse spark session list --workspace-name testsynapseworkspace --spark-pool-name testsparkpool
"""

helps['synapse spark session show'] = """
type: command
short-summary: Get a Spark session.
examples:
  - name: Get a Spark session.
    text: |-
        az synapse spark session show --livy-id 1 --workspace-name testsynapseworkspace --spark-pool-name testsparkpool
"""

helps['synapse spark session cancel'] = """
type: command
short-summary: Cancel a Spark session.
examples:
  - name: Cancel a Spark session.
    text: |-
        az synapse spark session cancel  --livy-id 1 --workspace-name testsynapseworkspace --spark-pool-name testsparkpool
"""

helps['synapse spark session reset-timeout'] = """
type: command
short-summary: Reset a Spark session timeout time.
examples:
  - name: Reset a Spark session's timeout time.
    text: |-
        az synapse spark session reset-timeout --livy-id 1 --workspace-name testsynapseworkspace --spark-pool-name testsparkpool
"""

helps['synapse spark statement'] = """
type: group
short-summary: Manage Synapse Spark statements.
"""

helps['synapse spark statement invoke'] = """
type: command
short-summary: Invoke a Spark statement.
examples:
  - name: Invoke a Spark statement.
    text: |-
        az synapse spark statement invoke --session-id 1 --workspace-name testsynapseworkspace \\
        --spark-pool-name testsparkpool --code "print('hello, Azure CLI')" --language pyspark
  - name: Submit a Spark statement by reading code content from file.
    text: |-
        az synapse spark statement invoke --session-id 1 --workspace-name testsynapseworkspace \\
        --spark-pool-name testsparkpool --code @file-path --language pyspark
"""

helps['synapse spark statement show'] = """
type: command
short-summary: Get a Spark statement.
examples:
  - name: Get a Spark statement.
    text: |-
        az synapse spark statement show --livy-id 1 --session-id 11 --workspace-name testsynapseworkspace \\
        --spark-pool-name testsparkpool
"""

helps['synapse spark statement list'] = """
type: command
short-summary: List all Spark statements
examples:
  - name: List all Spark statements.
    text: |-
        az synapse spark statement list --session-id 11 --workspace-name testsynapseworkspace \\
        --spark-pool-name testsparkpool
"""

helps['synapse spark statement cancel'] = """
type: command
short-summary: Cancel a Spark statement.
examples:
  - name: Cancel a Spark statement.
    text: |-
        az synapse spark statement cancel --livy-id 1 --session-id 11 --workspace-name testsynapseworkspace \\
        --spark-pool-name testsparkpool
"""

helps['synapse role'] = """
type: group
short-summary: Manage Synapse's role assignments and definitions.
"""

helps['synapse role scope'] = """
type: group
short-summary: Manage Synapse's role scopes.
"""

helps['synapse role scope list'] = """
type: command
short-summary: List role scopes.
examples:
  - name: List role scopes.
    text: |-
        az synapse role scope list --workspace-name testsynapseworkspace
"""

helps['synapse role assignment'] = """
type: group
short-summary: Manage Synapse's role assignments.
"""

helps['synapse role assignment show'] = """
type: command
short-summary: Get a role assignment by id.
examples:
  - name: Get a role assignment by id.
    text: |-
        az synapse role assignment show --workspace-name testsynapseworkspace \\
        --id 00000000-0000-0000-0000-000000000000
"""

helps['synapse role assignment list'] = """
type: command
short-summary: List role assignments.
examples:
  - name: List role assignments.
    text: |-
        az synapse role assignment list --workspace-name testsynapseworkspace
  - name: List role assignments by role id/name.
    text: |-
        az synapse role assignment list --workspace-name testsynapseworkspace \\
        --role "Synapse Apache Spark Administrator"
  - name: List role assignments by assignee.
    text: |-
        az synapse role assignment list --workspace-name testsynapseworkspace \\
        --assignee sp_name
  - name: List role assignments by objectId of the User, Group or Service Principal.
    text: |-
        az synapse role assignment list --workspace-name testsynapseworkspace \\
        --assignee-object-id 00000000-0000-0000-0000-000000000000
  - name: List role assignments by scope.
    text: |-
        az synapse role assignment list --workspace-name testsynapseworkspace \\
        --scope "workspaces/{workspaceName}"
  - name: List role assignments by item type and item name.
    text: |-
        az synapse role assignment list --workspace-name testsynapseworkspace \\
        --item-type "bigDataPools" --item "bigDataPoolName"
"""

helps['synapse role assignment create'] = """
type: command
short-summary: Create a role assignment.
examples:
  - name: Create a role assignment using service principal name.
    text: |-
        az synapse role assignment create --workspace-name testsynapseworkspace \\
        --role "Synapse Administrator" --assignee sp_name
  - name: Create a role assignment using user principal name.
    text: |-
        az synapse role assignment create --workspace-name testsynapseworkspace \\
        --role "Synapse Administrator" --assignee username@contoso.com
  - name: Create a role assignment using objectId of the User, Group or Service Principal.
    text: |-
        az synapse role assignment create --workspace-name testsynapseworkspace \\
        --role "Synapse Administrator" --assignee 00000000-0000-0000-0000-000000000000
  - name: Create a role assignment at scope.
    text: |-
        az synapse role assignment create --workspace-name testsynapseworkspace \\
        --scope "workspaces/{workspaceName}" --role "Synapse Administrator" --assignee username@contoso.com
  - name: Create a role assignment at scope that combination of item type and item name.
    text: |-
        az synapse role assignment create --workspace-name testsynapseworkspace \\
        --item-type "bigDataPools" --item "bigDataPoolName" --role "Synapse Administrator" \\
        --assignee username@contoso.com
"""

helps['synapse role assignment delete'] = """
type: command
short-summary: Delete role assignments of workspace.
examples:
  - name: Delete role assignments by role and assignee.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --role "Synapse Administrator" --assignee sp_name
  - name: Delete role assignments by role id/name.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --role "Synapse Administrator"
  - name: Delete role assignments by service principal name.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --assignee sp_name
  - name: Delete role assignments by user principal name.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --assignee username@contoso.com
  - name: Delete role assignments by objectId of the User, Group or Service Principal.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --assignee 00000000-0000-0000-0000-000000000001
  - name: Delete role assignments by ids.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --ids 10000000-0000-0000-0000-10000000-10000000-0000-0000-0000-10000000
  - name: Delete role assignments by scope.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --scope "workspaces/testsynapseworkspace/linkedServices/testlinkedServices"
"""

helps['synapse role definition'] = """
type: group
short-summary:  Manage Synapse's role definitions.
"""

helps['synapse role definition list'] = """
type: command
short-summary: List role definitions.
examples:
  - name: List role definitions.
    text: |-
        az synapse role definition list --workspace-name testsynapseworkspace
  - name: List role definitions built-in by Synapse.
    text: |-
        az synapse role definition list --workspace-name testsynapseworkspace --is-built-in True
"""

helps['synapse role definition show'] = """
type: command
short-summary: Get role definition by role id/name.
examples:
  - name: Get role definition by role id.
    text: |-
        az synapse role definition show --workspace-name testsynapseworkspace \\
        --role 00000000-0000-0000-0000-000000000000
  - name: Get role definition by role name.
    text: |-
        az synapse role definition show --workspace-name testsynapseworkspace \\
        --role "Synapse SQL Administrator"
"""

helps['synapse linked-service'] = """
type: group
short-summary: Manage Synapse's linked services.
"""

helps['synapse linked-service create'] = """
type: command
short-summary: Create a linked service.
examples:
  - name: Create a linked service. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse linked-service create --workspace-name testsynapseworkspace \\
          --name testlinkedservice --file @"path/linkedservice.json"
"""

helps['synapse linked-service update'] = """
type: command
short-summary: Update an exist linked service.
examples:
  - name: Update an exist linked service. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse linked-service update --workspace-name testsynapseworkspace \\
          --name testlinkedservice --file @"path/linkedservice.json"
"""

helps['synapse linked-service set'] = """
type: command
short-summary: Update an exist linked service.
examples:
  - name: Update an exist linked service. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse linked-service set --workspace-name testsynapseworkspace \\
          --name testlinkedservice --file @"path/linkedservice.json"
"""

helps['synapse linked-service show'] = """
type: command
short-summary: Get a linked service.
examples:
  - name: Get a linked service.
    text: |-
        az synapse linked-service show --workspace-name testsynapseworkspace \\
          --name testlinkedservice
"""

helps['synapse linked-service list'] = """
type: command
short-summary: List linked services.
examples:
  - name: List linked services.
    text: |-
        az synapse linked-service list --workspace-name testsynapseworkspace
"""

helps['synapse linked-service delete'] = """
type: command
short-summary: Delete a linked service.
examples:
  - name: Delete a linked service.
    text: |-
        az synapse linked-service delete --workspace-name testsynapseworkspace \\
          --name testlinkedservice
"""

helps['synapse dataset'] = """
type: group
short-summary: Manage Synapse's datasets.
"""

helps['synapse dataset create'] = """
type: command
short-summary: Create a dataset.
examples:
  - name: Create a dataset. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse dataset create --workspace-name testsynapseworkspace \\
          --name testdataset --file @"path/dataset.json"
"""

helps['synapse dataset update'] = """
type: command
short-summary: Update an exist dataset.
examples:
  - name: Update an exist dataset. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse dataset update --workspace-name testsynapseworkspace \\
          --name testdataset --file @"path/dataset.json"
"""

helps['synapse dataset set'] = """
type: command
short-summary: Update an exist dataset.
examples:
  - name: Update an exist dataset. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse dataset set --workspace-name testsynapseworkspace \\
          --name testdataset --file @"path/dataset.json"
"""

helps['synapse dataset show'] = """
type: command
short-summary: Get a dataset.
examples:
  - name: Get a dataset.
    text: |-
        az synapse dataset show --workspace-name testsynapseworkspace \\
          --name testdataset
"""

helps['synapse dataset list'] = """
type: command
short-summary: List datasets.
examples:
  - name: List datasets.
    text: |-
        az synapse dataset list --workspace-name testsynapseworkspace
"""

helps['synapse dataset delete'] = """
type: command
short-summary: Delete a dataset.
examples:
  - name: Delete a dataset.
    text: |-
        az synapse dataset delete --workspace-name testsynapseworkspace \\
          --name testdataset
"""

helps['synapse pipeline'] = """
type: group
short-summary: Manage Synapse's pipelines.
"""

helps['synapse pipeline create'] = """
type: command
short-summary: Create a pipeline.
examples:
  - name: Create a pipeline. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse pipeline create --workspace-name testsynapseworkspace \\
          --name testpipeline --file @"path/pipeline.json"
"""

helps['synapse pipeline update'] = """
type: command
short-summary: Update an exist pipeline.
examples:
  - name: Update an exist pipeline. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse pipeline update --workspace-name testsynapseworkspace \\
          --name testpipeline --file @"path/pipeline.json"
"""

helps['synapse pipeline set'] = """
type: command
short-summary: Update an exist pipeline.
examples:
  - name: Update an exist pipeline. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse pipeline set --workspace-name testsynapseworkspace \\
          --name testpipeline --file @"path/pipeline.json"
"""

helps['synapse pipeline show'] = """
type: command
short-summary: Get a pipeline.
examples:
  - name: Get a pipeline.
    text: |-
        az synapse pipeline show --workspace-name testsynapseworkspace \\
          --name testpipeline
"""

helps['synapse pipeline list'] = """
type: command
short-summary: List pipelines.
examples:
  - name: List pipelines.
    text: |-
        az synapse pipeline list --workspace-name testsynapseworkspace
"""

helps['synapse pipeline delete'] = """
type: command
short-summary: Delete a pipeline.
examples:
  - name: Delete a pipeline.
    text: |-
        az synapse pipeline delete --workspace-name testsynapseworkspace \\
          --name testpipeline
"""

helps['synapse pipeline create-run'] = """
type: command
short-summary: Creates a run of a pipeline.
examples:
  - name: Pipelines_CreateRun
    text: |-
        az synapse pipeline create-run --workspace-name testsynapseworkspace --name "myPipeline" \\
          --parameters "{\\"OutputBlobNameList\\":[\\"exampleoutput.csv\\"]}"
"""

helps['synapse pipeline-run'] = """
type: group
short-summary: Manage Synapse's pipeline run.
"""

helps['synapse pipeline-run show'] = """
type: command
short-summary: Get a pipeline run by its run ID.
examples:
  - name: Get a pipeline run by its run ID.
    text: |-
        az synapse pipeline-run show --workspace-name testsynapseworkspace \\
          --run-id "2f7fdb90-5df1-4b8e-ac2f-064cfa58202b"
"""

helps['synapse pipeline-run cancel'] = """
type: command
short-summary: Cancel a pipeline run by its run ID.
examples:
  - name: Cancel a pipeline run by its run ID.
    text: |-
        az synapse pipeline-run cancel --workspace-name testsynapseworkspace \\
          --run-id "16ac5348-ff82-4f95-a80d-638c1d47b721"
"""

helps['synapse pipeline-run query-by-workspace'] = """
type: command
short-summary: Query pipeline runs in the workspace based on input filter conditions.
examples:
  - name: Query pipeline runs in the workspace based on input filter conditions.
    text: |-
        az synapse pipeline-run query-by-workspace --workspace-name testsynapseworkspace --filters \\
          operand="PipelineName" operator="Equals" values="testpipeline" --last-updated-after "2020-09-03T00:36:44.3345758Z" \\
          --last-updated-before "2020-09-03T00:49:48.3686473Z"
"""

helps['synapse activity-run'] = """
type: group
short-summary: synapse activity-run
"""

helps['synapse activity-run query-by-pipeline-run'] = """
type: command
short-summary: Query activity runs based on input filter conditions.
examples:
  - name: Query activity runs based on input filter conditions.
    text: |-
        az synapse activity-run query-by-pipeline-run --workspace-name testsynapseworkspace \\
          --last-updated-after "2020-09-03T00:36:44.3345758Z" --last-updated-before "2020-09-03T00:49:48.3686473Z" \\
          --name testpipeline --run-id "53eeed66-ec46-11ea-8bd5-448500a5b1ac"
"""

helps['synapse trigger'] = """
type: group
short-summary: Manage Synapse's triggers.
"""

helps['synapse trigger create'] = """
type: command
short-summary: Create a trigger.
examples:
  - name: Create a trigger. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse trigger create --workspace-name testsynapseworkspace \\
          --name testtrigger --file @"path/trigger.json"
"""

helps['synapse trigger update'] = """
type: command
short-summary: Update an exist trigger.
examples:
  - name: Update an exist trigger. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse trigger update --workspace-name testsynapseworkspace \\
          --name testtrigger --file @"path/trigger.json"
"""

helps['synapse trigger set'] = """
type: command
short-summary: Update an exist trigger.
examples:
  - name: Update an exist trigger. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse trigger set --workspace-name testsynapseworkspace \\
          --name testtrigger --file @"path/trigger.json"
"""

helps['synapse trigger show'] = """
type: command
short-summary: Get a trigger.
examples:
  - name: Get a trigger.
    text: |-
        az synapse trigger show --workspace-name testsynapseworkspace \\
          --name testtrigger
"""

helps['synapse trigger list'] = """
type: command
short-summary: List triggers.
examples:
  - name: List triggers.
    text: |-
        az synapse trigger list --workspace-name testsynapseworkspace
"""

helps['synapse trigger delete'] = """
type: command
short-summary: Delete a trigger.
examples:
  - name: Delete a trigger.
    text: |-
        az synapse trigger delete --workspace-name testsynapseworkspace \\
          --name testtrigger
"""

helps['synapse trigger wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a trigger is met.
"""

helps['synapse trigger subscribe-to-event'] = """
type: command
short-summary: Subscribe event trigger to events.
examples:
  - name: Subscribe event trigger to events.
    text: |-
        az synapse trigger subscribe-to-event --workspace-name testsynapseworkspace \\
          --name eventtrigger
"""

helps['synapse trigger get-event-subscription-status'] = """
type: command
short-summary: Get a trigger's event subscription status.
examples:
  - name:  Get a trigger's event subscription status.
    text: |-
        az synapse trigger get-event-subscription-status --workspace-name testsynapseworkspace \\
          --name eventtrigger
"""

helps['synapse trigger unsubscribe-from-event'] = """
type: command
short-summary: Unsubscribe event trigger from events.
examples:
  - name: Unsubscribe event trigger from events.
    text: |-
        az synapse trigger unsubscribe-from-event --workspace-name testsynapseworkspace \\
          --name eventtrigger
"""

helps['synapse trigger start'] = """
type: command
short-summary: Starts a trigger.
examples:
  - name: Starts a trigger.
    text: |-
        az synapse trigger start --workspace-name testsynapseworkspace \\
          --name testtrigger
"""

helps['synapse trigger stop'] = """
type: command
short-summary: Stops a trigger.
examples:
  - name: Stops a trigger.
    text: |-
        az synapse trigger stop --workspace-name testsynapseworkspace \\
          --name testtrigger
"""

helps['synapse trigger-run'] = """
    type: group
    short-summary: synapse trigger-run
"""

helps['synapse trigger-run rerun'] = """
type: command
short-summary: Rerun single trigger instance by runId.
examples:
  - name: Rerun single trigger instance by runId.
    text: |-
        az synapse trigger-run rerun --workspace-name testsynapseworkspace \\
          --name testtrigger --run-id 08586024068106001417583731803CU31
"""

helps['synapse trigger-run cancel'] = """
type: command
short-summary: Cancel a single trigger instance by runId.
examples:
  - name: Cancel a single trigger instance by runId.
    text: |-
        az synapse trigger-run cancel --workspace-name testsynapseworkspace \\
          --name testtrigger --run-id 08586024068106001417583731803CU31
"""

helps['synapse trigger-run query-by-workspace'] = """
type: command
short-summary: Query trigger runs in the workspace based on input filter conditions.
examples:
  - name: Query trigger runs in the workspace based on input filter conditions.
    text: |-
        az synapse trigger-run query-by-workspace --workspace-name testsynapseworkspace --filters \\
          operand="TriggerName" operator="Equals" values="testtrigger" --last-updated-after "2020-09-03T00:36:44.3345758Z" \\
          --last-updated-before "2020-09-03T00:49:48.3686473Z"
"""

helps['synapse data-flow'] = """
type: group
short-summary: Manage Synapse's data flows.
"""

helps['synapse data-flow create'] = """
type: command
short-summary: Create a data flow.
examples:
  - name: Create a data flow. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse data-flow create --workspace-name testsynapseworkspace \\
          --name testdataflow --file @"path/dataflow.json"
"""

helps['synapse data-flow set'] = """
type: command
short-summary: Set an exist data flow.
examples:
  - name: Set an exist data flow. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse data-flow set --workspace-name testsynapseworkspace \\
          --name testdataflow --file @"path/dataflow.json"
"""

helps['synapse data-flow show'] = """
type: command
short-summary: Get a data flow.
examples:
  - name: Get a data flow.
    text: |-
        az synapse data-flow show --workspace-name testsynapseworkspace \\
          --name testdataflow
"""

helps['synapse data-flow list'] = """
type: command
short-summary: List data flows.
examples:
  - name: List data flows.
    text: |-
        az synapse data-flow list --workspace-name testsynapseworkspace
"""

helps['synapse data-flow delete'] = """
type: command
short-summary: Delete a data flow.
examples:
  - name: Delete a data flow.
    text: |-
        az synapse data-flow delete --workspace-name testsynapseworkspace \\
          --name testdataflow
"""

helps['synapse notebook'] = """
type: group
short-summary: Manage Synapse's notebooks.
"""

helps['synapse notebook create'] = """
type: command
short-summary: Create a notebook.
examples:
  - name: Create a notebook. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse notebook create --workspace-name testsynapseworkspace \\
          --name testnotebook --file @"path/notebook.ipynb" --folder-path 'folder/subfolder'
"""

helps['synapse notebook set'] = """
type: command
short-summary: Set an exist notebook.
examples:
  - name: Set an exist notebook. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse notebook set --workspace-name testsynapseworkspace \\
          --name testnotebook --file @"path/notebook.ipynb" --folder-path 'folder/subfolder'
"""

helps['synapse notebook import'] = """
type: command
short-summary: Import a notebook.
examples:
  - name: Import a notebook. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse notebook import --workspace-name testsynapseworkspace \\
          --name testnotebook --file @"path/notebook.ipynb" --folder-path 'folder/subfolder'
"""

helps['synapse notebook show'] = """
type: command
short-summary: Get a notebook.
examples:
  - name: Get a notebook.
    text: |-
        az synapse notebook show --workspace-name testsynapseworkspace \\
          --name testnotebook
"""

helps['synapse notebook list'] = """
type: command
short-summary: List notebooks.
examples:
  - name: List notebooks.
    text: |-
        az synapse notebook list --workspace-name testsynapseworkspace
"""

helps['synapse notebook export'] = """
type: command
short-summary: Export notebooks.
examples:
  - name: Export a notebook.
    text: |-
        az synapse notebook export --workspace-name testsynapseworkspace \\
          --name testnotebook --output-folder C:/output
  - name: Export all notebooks under a workspace.
    text: |-
        az synapse notebook export --workspace-name testsynapseworkspace \\
          --output-folder C:/output
"""

helps['synapse notebook delete'] = """
type: command
short-summary: Delete a notebook.
examples:
  - name: Delete a notebook.
    text: |-
        az synapse notebook delete --workspace-name testsynapseworkspace \\
          --name testnotebook
"""
helps['synapse workspace-package'] = """
type: group
short-summary: Manage Synapse's workspace packages.
"""

helps['synapse workspace-package upload'] = """
type: command
short-summary: Upload a local workspace package file to an Azure Synapse workspace.
examples:
  - name: Upload a local workspace package file to an Azure Synapse workspace.
    text: |-
        az synapse workspace-package upload --workspace-name testsynapseworkspace \\
          --package C:/package.jar
"""

helps['synapse workspace-package upload-batch'] = """
type: command
short-summary: Upload workspace package files from a local directory to an Azure Synapse workspace.
examples:
  - name: Upload workspace package files from a local directory to an Azure Synapse workspace.
    text: |-
        az synapse workspace-package upload-batch --workspace-name testsynapseworkspace \\
          --source C:/package
"""

helps['synapse workspace-package show'] = """
type: command
short-summary: Get a workspace package.
examples:
  - name: Get a workspace package.
    text: |-
        az synapse workspace-package show --workspace-name testsynapseworkspace \\
          --name testpackage.jar
"""

helps['synapse workspace-package list'] = """
type: command
short-summary: List workspace packages.
examples:
  - name: List workspace packages.
    text: |-
        az synapse workspace-package list --workspace-name testsynapseworkspace
"""

helps['synapse workspace-package delete'] = """
type: command
short-summary: Delete a workspace package.
examples:
  - name: Delete a workspace package.
    text: |-
        az synapse workspace-package delete --workspace-name testsynapseworkspace \\
          --name testpackage.jar
"""

helps['synapse integration-runtime'] = """
type: group
short-summary: Manage Synapse's integration runtimes.
"""

helps['synapse integration-runtime managed'] = """
    type: group
    short-summary: Manage integration runtime with synapse sub group managed
"""

helps['synapse integration-runtime managed create'] = """
type: command
short-summary: Create an managed integration runtime.
examples:
  - name: Create an managed integration runtime.
    text: |-
        az synapse integration-runtime managed create --workspace-name testsynapseworkspace --resource-group rg \\
          --name testintegrationruntime
"""

helps['synapse integration-runtime self-hosted'] = """
    type: group
    short-summary: Manage integration runtime with synapse sub group self-hosted
"""

helps['synapse integration-runtime self-hosted create'] = """
type: command
short-summary: Create an self-hosted integration runtime.
examples:
  - name: Create an self-hosted integration runtime.
    text: |-
        az synapse integration-runtime self-hosted create --workspace-name testsynapseworkspace --resource-group rg \\
          --name testintegrationruntime
"""

helps['synapse integration-runtime create'] = """
type: command
short-summary: Create an integration runtime.
examples:
  - name: Create an integration runtime.
    text: |-
        az synapse integration-runtime create --workspace-name testsynapseworkspace --resource-group rg \\
          --name testintegrationruntime --type Managed
"""

helps['synapse integration-runtime update'] = """
type: command
short-summary: Update an integration runtime.
examples:
  - name: Update an integration runtime.
    text: |-
        az synapse integration-runtime update --workspace-name testsynapseworkspace --resource-group rg \\
          --name testintegrationruntime --auto-update On --update-delay-offset '\"PT03H\"'
"""

helps['synapse integration-runtime show'] = """
type: command
short-summary: Get an integration runtime.
examples:
  - name: Get an integration runtime.
    text: |-
        az synapse integration-runtime show --workspace-name testsynapseworkspace --resource-group rg \\
          --name testintegrationruntime
"""

helps['synapse integration-runtime list'] = """
type: command
short-summary: List integration runtimes.
examples:
  - name: List integration runtimes.
    text: |-
        az synapse integration-runtime list --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse integration-runtime delete'] = """
type: command
short-summary: Delete an integration runtime.
examples:
  - name: Delete an integration runtime.
    text: |-
        az synapse integration-runtime delete --workspace-name testsynapseworkspace --resource-group rg \\
          --name testintegrationruntime
"""

helps['synapse integration-runtime wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a integration runtime is met.
"""

helps['synapse integration-runtime upgrade'] = """
type: command
short-summary: Upgrade self-hosted integration runtime.
examples:
  - name: Upgrade self-hosted integration runtime.
    text: |-
        az synapse integration-runtime upgrade --workspace-name testsynapseworkspace --resource-group rg \\
          --name testintegrationruntime
"""

helps['synapse integration-runtime list-auth-key'] = """
type: command
short-summary: Get keys for a self-hosted integration runtime.
examples:
  - name: Get keys for a self-hosted integration runtime.
    text: |-
        az synapse integration-runtime list-auth-key --workspace-name testsynapseworkspace --resource-group rg \\
          --name selfhostedintegrationruntime
"""

helps['synapse integration-runtime regenerate-auth-key'] = """
type: command
short-summary: Regenerate self-hosted integration runtime key.
examples:
  - name: Regenerate self-hosted integration runtime key.
    text: |-
        az synapse integration-runtime regenerate-auth-key --workspace-name testsynapseworkspace --resource-group rg \\
          --name selfhostedintegrationruntime --key-name authKey1
"""

helps['synapse integration-runtime get-monitoring-data'] = """
type: command
short-summary: Get metric data for a self-hosted integration runtime.
examples:
  - name: Get metric data for a self-hosted integration runtime.
    text: |-
        az synapse integration-runtime get-monitoring-data --workspace-name testsynapseworkspace --resource-group rg \\
          --name selfhostedintegrationruntime
"""

helps['synapse integration-runtime sync-credentials'] = """
type: command
short-summary: Synchronize credentials among integration runtime nodes.
examples:
  - name: Synchronize credentials among integration runtime nodes.
    text: |-
        az synapse integration-runtime sync-credentials --workspace-name testsynapseworkspace --resource-group rg \\
          --name selfhostedintegrationruntime
"""

helps['synapse integration-runtime get-connection-info'] = """
type: command
short-summary: Get the integration runtime connection infomation.
examples:
  - name: Get the integration runtime connection infomation.
    text: |-
        az synapse integration-runtime get-connection-info --workspace-name testsynapseworkspace --resource-group rg \\
          --name selfhostedintegrationruntime
"""

helps['synapse integration-runtime get-status'] = """
type: command
short-summary: Gets detailed status information for an integration runtime.
examples:
  - name: Gets detailed status information for an integration runtime.
    text: |-
        az synapse integration-runtime get-status --workspace-name testsynapseworkspace --resource-group rg \\
          --name selfhostedintegrationruntime
"""

helps['synapse integration-runtime start'] = """
type: command
short-summary: start an SSIS integration runtime.
examples:
  - name: start an SSIS integration runtime.
    text: |-
        az synapse integration-runtime start --workspace-name testsynapseworkspace --resource-group rg \\
          --name testintegrationruntime
"""

helps['synapse integration-runtime stop'] = """
type: command
short-summary: stop an SSIS integration runtime.
examples:
  - name: stop an SSIS integration runtime.
    text: |-
        az synapse integration-runtime stop --workspace-name testsynapseworkspace --resource-group rg \\
          --name testintegrationruntime
"""

helps['synapse integration-runtime-node'] = """
type: group
short-summary: Manage Synapse's self-hosted integration runtime nodes.
"""

helps['synapse integration-runtime-node show'] = """
type: command
short-summary: Get self-hosted integration runtime node information.
examples:
  - name: Get self-hosted integration runtime node information.
    text: |-
        az synapse integration-runtime-node show --workspace-name testsynapseworkspace --resource-group rg \\
          --name selfhostedintegrationruntime --node-name testnode
"""

helps['synapse integration-runtime-node update'] = """
type: command
short-summary: Update self-hosted integration runtime node.
examples:
  - name: Update self-hosted integration runtime node.
    text: |-
        az synapse integration-runtime-node update --workspace-name testsynapseworkspace --resource-group rg \\
          --name selfhostedintegrationruntime --node-name testnode --auto-update On --update-delay-offset 'PT03H'
"""

helps['synapse integration-runtime-node delete'] = """
type: command
short-summary: Remove a self-hosted integration runtime node.
examples:
  - name: Remove a self-hosted integration runtime node.
    text: |-
        az synapse integration-runtime-node delete --workspace-name testsynapseworkspace --resource-group rg \\
          --name selfhostedintegrationruntime --node-name testnode
"""

helps['synapse integration-runtime-node get-ip-address'] = """
type: command
short-summary: Get self-hosted integration runtime node ip.
examples:
  - name: Get self-hosted integration runtime node ip.
    text: |-
        az synapse integration-runtime-node get-ip-address --workspace-name testsynapseworkspace --resource-group rg \\
          --name selfhostedintegrationruntime --node-name testnode
"""

helps['synapse managed-private-endpoints'] = """
type: group
short-summary: Manage synapse managed private endpoints.
"""

helps['synapse managed-private-endpoints show'] = """
type: command
short-summary: Get a synapse managed private endpoints.
examples:
  - name: Get a synapse managed private endpoints.
    text: |-
        az synapse managed-private-endpoints show --workspace-name testsynapseworkspace \\
          --pe-name testendpointname
"""

helps['synapse managed-private-endpoints create'] = """
type: command
short-summary: Create a synapse managed private endpoints.
examples:
  - name: Create a synapse managed private endpoints. Definition file should contains privateLinkResourceId and groupId.
    text: |-
        az synapse managed-private-endpoints create --workspace-name testsynapseworkspace \\
          --pe-name testendpointname \\
          --file @path/test.json
"""

helps['synapse managed-private-endpoints list'] = """
type: command
short-summary: List synapse managed private endpoints in a workspace.
examples:
  - name: List a synapse managed private endpoints.
    text: |-
        az synapse managed-private-endpoints list --workspace-name testsynapseworkspace
"""

helps['synapse managed-private-endpoints delete'] = """
type: command
short-summary: delete synapse managed private endpoints in a workspace.
examples:
  - name: Delete a synapse managed private endpoints.
    text: |-
        az synapse managed-private-endpoints delete --workspace-name testsynapseworkspace \\
          --pe-name testendpointname
"""

helps['synapse spark-job-definition'] = """
type: group
short-summary: Manage spark job definitions in a synapse workspace.
"""

helps['synapse spark-job-definition show'] = """
type: command
short-summary: Get a spark job definition.
examples:
  - name: Get a spark job definition.
    text: |-
        az synapse spark-job-definition show --workspace-name testsynapseworkspace \\
          --name testsjdname
"""

helps['synapse spark-job-definition list'] = """
type: command
short-summary: List spark job definitions.
examples:
  - name: List spark job definitions.
    text: |-
        az synapse spark-job-definition list --workspace-name testsynapseworkspace
"""

helps['synapse spark-job-definition delete'] = """
type: command
short-summary: Delete a spark job definition.
examples:
  - name: Delete a spark job definition.
    text: |-
        az synapse spark-job-definition delete --workspace-name testsynapseworkspace \\
          --name testsjdname
"""

helps['synapse spark-job-definition create'] = """
type: command
short-summary: Create a spark job definition.
examples:
  - name: Create a spark job definition. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse spark-job-definition create --workspace-name testsynapseworkspace \\
          --name testsjdname --file @"path/test.json" --folder-path 'folder/subfolder'
"""

helps['synapse spark-job-definition update'] = """
type: command
short-summary: Update a spark job definition.
examples:
  - name: Update a spark job definition. Pay attention to add "@" at the front of the file path as the best practice for complex arguments like JSON string.
    text: |-
        az synapse spark-job-definition update --workspace-name testsynapseworkspace \\
          --name testsjdname --file @"path/test.json" --folder-path 'folder/subfolder'
"""

helps['synapse spark-job-definition wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a spark job definition is met.
"""

helps['synapse kusto pool add-language-extension'] = """
    type: command
    short-summary: "Add a list of language extensions that can run within KQL queries."
    parameters:
      - name: --value
        short-summary: "The list of language extensions."
        long-summary: |
            Usage: --value language-extension-name=XX

            language-extension-name: The language extension name.

            Multiple actions can be specified by using more than one --value argument.
    examples:
      - name: KustoPoolAddLanguageExtensions
        text: |-
               az synapse kusto pool add-language-extension --name "kustoclusterrptest4" --value \
language-extension-name="PYTHON" --value language-extension-name="R" --resource-group "kustorptest" --workspace-name \
"kustorptest"
"""

helps['synapse kusto pool detach-follower-database'] = """
    type: command
    short-summary: "Detaches all followers of a database owned by this Kusto Pool."
    examples:
      - name: KustoPoolDetachFollowerDatabases
        text: |-
               az synapse kusto pool detach-follower-database --attached-database-configuration-name \
"myAttachedDatabaseConfiguration" --kusto-pool-resource-id "/subscriptions/12345678-1234-1234-1234-123456789098/resourc\
eGroups/kustorptest/providers/Microsoft.Synapse/workspaces/kustorptest/kustoPools/leader4" --name \
"kustoclusterrptest4" --resource-group "kustorptest" --workspace-name "kustorptest"
"""

helps['synapse kusto pool remove-language-extension'] = """
    type: command
    short-summary: "Remove a list of language extensions that can run within KQL queries."
    parameters:
      - name: --value
        short-summary: "The list of language extensions."
        long-summary: |
            Usage: --value language-extension-name=XX

            language-extension-name: The language extension name.

            Multiple actions can be specified by using more than one --value argument.
    examples:
      - name: KustoPoolRemoveLanguageExtensions
        text: |-
               az synapse kusto pool remove-language-extension --name "kustoclusterrptest4" --value \
language-extension-name="PYTHON" --value language-extension-name="R" --resource-group "kustorptest" --workspace-name \
"kustorptest"
"""

helps['synapse kusto pool list-language-extension'] = """
    type: command
    short-summary: "Returns a list of language extensions that can run within KQL queries."
    examples:
      - name: KustoPoolListLanguageExtensions
        text: |-
               az synapse kusto pool list-language-extension --name "kustoclusterrptest4" --resource-group \
"kustorptest" --workspace-name "kustorptest"
"""

helps['synapse kusto pool create'] = """
    type: command
    short-summary: "Create a Kusto pool."
    parameters:
      - name: --sku
        short-summary: "The SKU of the kusto pool."
        long-summary: |
            Usage: --sku name=XX capacity=XX size=XX

            name: Required. SKU name.
            capacity: The number of instances of the cluster.
            size: Required. SKU size.
      - name: --optimized-autoscale
        short-summary: "Optimized auto scale definition."
        long-summary: |
            Usage: --optimized-autoscale version=XX is-enabled=XX minimum=XX maximum=XX

            version: Required. The version of the template defined, for instance 1.
            is-enabled: Required. A boolean value that indicate if the optimized autoscale feature is enabled or not.
            minimum: Required. Minimum allowed instances count.
            maximum: Required. Maximum allowed instances count.
    examples:
      - name: kustoPoolsCreateOrUpdate
        text: |-
               az synapse kusto pool create --name "kustoclusterrptest4" --location "westus" --enable-purge true \
--enable-streaming-ingest true --workspace-uid "11111111-2222-3333-444444444444" --sku name="Storage optimized" \
capacity=2 size="Medium" --resource-group "kustorptest" --workspace-name "synapseWorkspaceName"
"""

helps['synapse kusto pool update'] = """
    type: command
    short-summary: "Update a Kusto Kusto Pool."
    parameters:
      - name: --sku
        short-summary: "The SKU of the kusto pool."
        long-summary: |
            Usage: --sku name=XX capacity=XX size=XX

            name: Required. SKU name.
            capacity: The number of instances of the cluster.
            size: Required. SKU size.
      - name: --optimized-autoscale
        short-summary: "Optimized auto scale definition."
        long-summary: |
            Usage: --optimized-autoscale version=XX is-enabled=XX minimum=XX maximum=XX

            version: Required. The version of the template defined, for instance 1.
            is-enabled: Required. A boolean value that indicate if the optimized autoscale feature is enabled or not.
            minimum: Required. Minimum allowed instances count.
            maximum: Required. Maximum allowed instances count.
    examples:
      - name: kustoPoolsUpdate
        text: |-
               az synapse kusto pool update --name "kustoclusterrptest4" --enable-purge true --enable-streaming-ingest \
true --workspace-uid "11111111-2222-3333-444444444444" --sku name="Storage optimized" capacity=2 size="Medium" \
--resource-group "kustorptest" --workspace-name "synapseWorkspaceName"
"""

helps['synapse kusto'] = """
    type: group
    short-summary: "Manage synapse kusto"
"""


helps['synapse kql-script'] = """
    type: group
    short-summary: Manage script with kusto
"""

helps['synapse kql-script show'] = """
    type: command
    short-summary: "Gets a KQL script."
    examples:
      - name: KustoScriptsGet
        text: |-
               az synapse kql-script show --workspace-name "kustoWorkspaceName" --name "kustoScript1"
"""

helps['synapse kql-script list'] = """
    type: command
    short-summary: "List KQL scripts."
    examples:
      - name: KustoScriptsList
        text: |-
               az synapse kql-script list --workspace-name "kustoWorkspaceName"
"""

helps['synapse kql-script create'] = """
    type: command
    short-summary: "Creates a KQL script."
    examples:
      - name: KustoScriptsCreateOrUpdate
        text: |-
               az synapse kql-script create --resource-group "kustorptest" --workspace-name "kustoWorkspaceName" \
               --kusto-pool-name kustopooltest --kusto-database-name kustodbtest --file C:\\samples\\KqlScript.kql \
               --name "kustoScript1"
"""

helps['synapse kql-script import'] = """
    type: command
    short-summary: "Creates a KQL script."
    examples:
      - name: KustoScriptsCreateOrUpdate
        text: |-
               az synapse kql-script import --resource-group "kustorptest" --workspace-name "kustoWorkspaceName" \
               --kusto-pool-name kustopooltest --kusto-database-name kustodbtest --file C:\\samples\\KqlScript.kql \
               --name "kustoScript1"
"""

helps['synapse kql-script export'] = """
    type: command
    short-summary: "Export KQL scripts."
    examples:
      - name: KustoScriptsExport
        text: |-
               az synapse kql-script export --workspace-name "kustoWorkspaceName" --output-folder "C:\\KqlScirpt"
"""

helps['synapse kql-script delete'] = """
    type: command
    short-summary: "Deletes a KQL script"
    examples:
      - name: KustoScriptsDelete
        text: |-
               az synapse kql-script delete --workspace-name "kustoWorkspaceName" --name "kustoScript1"
"""

helps['synapse kql-script wait'] = """
    type: command
    short-summary: "Place the CLI in a waiting state until a condition of a KQL script is met."
"""

helps['synapse sql-script'] = """
type: group
short-summary: Manage SQL scripts in a synapse workspace.
"""

helps['synapse sql-script list'] = """
type: command
short-summary: List SQL scripts in a synapse workspace.
examples:
  - name: List SQL scripts.
    text: |-
        az synapse sql-script list --workspace-name testsynapseworkspace
"""

helps['synapse sql-script show'] = """
type: command
short-summary: Get a SQL script.
examples:
  - name: Get a SQL script.
    text: |-
        az synapse sql-script show --workspace-name testsynapseworkspace \\
          --name testsqlscriptname
"""

helps['synapse sql-script delete'] = """
type: command
short-summary: Delete a SQL script.
examples:
  - name: Delete a SQL script.
    text: |-
        az synapse sql-script delete --workspace-name testsynapseworkspace \\
          --name testsqlscriptname
"""

helps['synapse sql-script create'] = """
type: command
short-summary: Create or update a SQL script.
examples:
  - name: Create a SQL script.
    text: |-
        az synapse sql-script create --workspace-name testsynapseworkspace \\
          --name testsqlscriptname \\
          --file 'path/test.sql'
"""

helps['synapse sql-script export'] = """
type: command
short-summary: Export a SQL script.
examples:
  - name: Export a SQL script.
    text: |-
        az synapse sql-script export --workspace-name testsynapseworkspace \\
          --name testsqlscriptname \\
          --output-folder 'path/folder'
"""

helps['synapse sql-script wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a sql script is met.
"""

helps['synapse sql-script import'] = """
type: command
short-summary: Import a SQL script.
examples:
  - name: Import a SQL script.
    text: |-
        az synapse sql-script import --workspace-name testsynapseworkspace \\
          --name testsqlscriptname \\
          --file 'path/test.sql'
"""

helps['synapse link-connection'] = """
type: group
short-summary: Manage Synapse's link connection.
"""

helps['synapse link-connection list'] = """
type: command
short-summary: List link connections in a synapse workspace.
examples:
  - name: List link connections.
    text: |-
        az synapse link-connection list --workspace-name testsynapseworkspace
"""

helps['synapse link-connection show'] = """
type: command
short-summary: Get a link connection.
examples:
  - name: Get a link-connection.
    text: |-
        az synapse link-connection show --workspace-name testsynapseworkspace \\
          --name testlinkconectionname
"""

helps['synapse link-connection delete'] = """
type: command
short-summary: Delete a link connection.
examples:
  - name: Delete a link connection.
    text: |-
        az synapse link-connection delete --workspace-name testsynapseworkspace \\
          --name testlinkconnectionname
"""

helps['synapse link-connection create'] = """
type: command
short-summary: Create a link connection.
examples:
  - name: Create a link connection.
    text: |-
        az synapse link-connection create --workspace-name testsynapseworkspace \\
          --name testlinkconnectionname \\
          --file @"path/definition.json"
"""

helps['synapse link-connection update'] = """
type: command
short-summary: Update a link connection.
examples:
  - name: Update a link connnection.
    text: |-
        az synapse link-connection update --workspace-name testsynapseworkspace \\
          --name testlinkconnectionname \\
          --file @"path/definition.json"
"""

helps['synapse link-connection start'] = """
type: command
short-summary: Start a link connnection.
examples:
  - name: Start a link connection.
    text: |-
        az synapse link-connection start --workspace-name testsynapseworkspace \\
          --name testlinkconnectionname"
"""

helps['synapse link-connection stop'] = """
type: command
short-summary: Stop a link connection.
examples:
  - name: Stop a link connection.
    text: |-
        az synapse link-connection stop --workspace-name testsynapseworkspace \\
          --name testlinkconnectionname
"""

helps['synapse link-connection get-status'] = """
type: command
short-summary: check a link connection status after start/stop a link connection.
examples:
  - name: Stop a link connection.
    text: |-
        az synapse link-connection get-status --workspace-name testsynapseworkspace \\
          --name testlinkconnectionname
"""