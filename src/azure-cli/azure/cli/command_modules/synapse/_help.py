# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

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
        az synapse workspace create --name fromcli4 --resource-group rg \\
          --storage-account testadlsgen2 --file-system testfilesystem \\
          --sql-admin-login-user cliuser1 --sql-admin-login-password Password123! --location "East US"
  - name: Create a Synapse workspace with storage resource id
    text: |-
        az synapse workspace create --name fromcli4 --resource-group rg \\
          --storage-account /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/testadlsgen2 --file-system testfilesystem \\
          --sql-admin-login-user cliuser1 --sql-admin-login-password Password123! --location "East US"
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
        --spark-version 2.4 --node-count 3 --node-size Medium
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
        az synapse sql pool create --name sqlpoolcli1 --performance-level "DW1000c" \\
        --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool show'] = """
type: command
short-summary: Get a SQL pool.
examples:
  - name: Get a SQL pool.
    text: |-
        az synapse sql pool show --name sqlpoolcli1 --workspace-name testsynapseworkspace --resource-group rg
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
        az synapse sql pool update --name sqlpoolcli1 --workspace-name testsynapseworkspace --resource-group rg \\
        --tags key1=value1
"""

helps['synapse sql pool pause'] = """
type: command
short-summary: Pause a SQL pool.
examples:
  - name: Pause a SQL pool.
    text: |-
        az synapse sql pool pause --name sqlpoolcli1 --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool resume'] = """
type: command
short-summary: Resume a SQL pool.
examples:
  - name: Resume a SQL pool.
    text: |-
        az synapse sql pool resume --name sqlpoolcli1 --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool delete'] = """
type: command
short-summary: Delete a SQL pool.
examples:
  - name: Delete a SQL pool.
    text: |-
        az synapse sql pool delete --name sqlpoolcli1 --workspace-name testsynapseworkspace --resource-group rg
"""

helps['synapse sql pool wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a SQL pool is met.
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
        --role "Sql Admin"
  - name: List role assignments by assignee.
    text: |-
        az synapse role assignment list --workspace-name testsynapseworkspace \\
        --assignee sp_name
  - name: List role assignments by objectId of the User, Group or Service Principal.
    text: |-
        az synapse role assignment list --workspace-name testsynapseworkspace \\
        --assignee 00000000-0000-0000-0000-000000000000
"""

helps['synapse role assignment create'] = """
type: command
short-summary: Create a role assignment.
examples:
  - name: Create a role assignment using service principal name.
    text: |-
        az synapse role assignment create --workspace-name testsynapseworkspace \\
        --role "Sql Admin" --assignee sp_name
  - name: Create a role assignment using user principal name.
    text: |-
        az synapse role assignment create --workspace-name testsynapseworkspace \\
        --role "Sql Admin" --assignee username@consoso.com
  - name: Create a role assignment using objectId of the User, Group or Service Principal.
    text: |-
        az synapse role assignment create --workspace-name testsynapseworkspace \\
        --role "Sql Admin" --assignee 00000000-0000-0000-0000-000000000000
"""

helps['synapse role assignment delete'] = """
type: command
short-summary: Delete role assignments of workspace.
examples:
  - name: Delete role assignments by role id/name.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --role "Sql Admin"
  - name: Delete role assignments by service principal name.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --assignee sp_name
  - name: Delete role assignments by user principal name.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --assignee username@consoso.com
  - name: Delete role assignments by objectId of the User, Group or Service Principal.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --assignee 00000000-0000-0000-0000-000000000001
  - name: Delete role assignments by ids.
    text: |-
        az synapse role assignment delete --workspace-name testsynapseworkspace \\
        --ids 10000000-0000-0000-0000-10000000-10000000-0000-0000-0000-10000000
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
"""

helps['synapse role definition show'] = """
type: command
short-summary: Get role definition by role id/name.
examples:
  - name: Get role definition by role id.
    text: |-
        az synapse role definition show --workspace-name testsynapseworkspace \\
        --role 00000000-0000-0000-0000-000000000000
"""
