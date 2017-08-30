# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['dla'] = """
    type: group
    short-summary: Manage Data Lake Analytics accounts, jobs, and catalogs.
    long-summary: These commands are in preview.
"""

helps['dla job'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics jobs.
    long-summary: These commands are in preview.
"""

helps['dla job submit'] = """
    type: command
    short-summary: Submits a job to a Data Lake Analytics account.
    parameters:
        - name: --job-name
          type: string
          short-summary: 'Name for the submitted job.'
        - name: --script
          type: string
          short-summary: 'Script to submit.'
          long-summary: This is either an inline script, or `@<file path>` to load from a file.
        - name: --runtime-version
          short-summary: 'The runtime version to use.'
          long-summary: This parameter is used for explicitly overwriting the default runtime. It should only be done if you know what you are doing.
        - name: --degree-of-parallelism
          short-summary: 'The degree of parallelism for the job.'
          long-summary: Higher values equate to more parallelism and will usually yield faster running jobs, at the cost of more AUs.
        - name: --priority
          short-summary: 'The priority of the job.'
          long-summary: Lower values increase the priority, with the lowest value being 1. This determines the order jobs are run in.

"""

helps['dla job cancel'] = """
    type: command
    short-summary: Cancels a Data Lake Analytics job.
"""

helps['dla job show'] = """
    type: command
    short-summary: Shows information for a Data Lake Analytics job.
"""

helps['dla job wait'] = """
    type: command
    short-summary: Waits for a Data Lake Analytics job to finish.
    long-summary: This command exits when the job completes.
    parameters:
        - name: --job-id
          type: string
          short-summary: 'Job ID to poll for completion.'
"""

helps['dla job list'] = """
    type: command
    short-summary: Lists Data Lake Analytics jobs.
"""

helps['dla catalog'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalogs.
    long-summary: These commands are in preview.
"""

helps['dla catalog database'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog databases.
    long-summary: These commands are in preview.
"""

helps['dla catalog assembly'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog assemblies.
    long-summary: These commands are in preview.
"""

helps['dla catalog external-data-source'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog external data sources.
    long-summary: These commands are in preview.
"""

helps['dla catalog procedure'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog stored procedures.
    long-summary: These commands are in preview.
"""

helps['dla catalog schema'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog schemas.
    long-summary: These commands are in preview.
"""

helps['dla catalog table'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog tables.
    long-summary: These commands are in preview.
"""

helps['dla catalog table list'] = """
    type: command
    short-summary: List tables in the database or schema.
    parameters:
        - name: --database-name
          type: string
          short-summary: 'The name of the database.'
        - name: --schema-name
          type: string
          short-summary: 'The schema assocated with the tables to list.'
"""

helps['dla catalog table-partition'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog table partitions.
    long-summary: These commands are in preview.
"""

helps['dla catalog table-stats'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog table statistics.
    long-summary: These commands are in preview.
"""

helps['dla catalog table-stats list'] = """
    type: command
    short-summary: Lists table statistics in the database, a table, or a schema.
    parameters:
        - name: --database-name
          type: string
          short-summary: 'The name of the database.'
        - name: --schema-name
          type: string
          short-summary: 'The schema associated with the tables to list.'
        - name: --table-name
          type: string
          short-summary: 'The table to list statistics for. --schema-name must also be specified.'
"""

helps['dla catalog table-type'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog table types.
    long-summary: These commands are in preview.
"""

helps['dla catalog tvf'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog table valued functions.
    long-summary: These commands are in preview.
"""

helps['dla catalog tvf list'] = """
    type: command
    short-summary: Lists table valued functions in a database or schema.
    parameters:
        - name: --database-name
          type: string
          short-summary: 'The name of the database.'
        - name: --schema-name
          type: string
          short-summary: 'The name of the schema assocated with table valued functions to list.'
"""

helps['dla catalog view'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog views.
    long-summary: These commands are in preview.
"""

helps['dla catalog view list'] = """
    type: command
    short-summary: Lists views in a database or schema.
    parameters:
        - name: --database-name
          type: string
          short-summary: 'The name of the database.'
        - name: --schema-name
          type: string
          short-summary: 'The name of the schema associated with the views to list.'
"""

helps['dla catalog credential'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog credentials.
    long-summary: These commands are in preview.
"""

helps['dla catalog credential create'] = """
    type: command
    short-summary: Creates a new catalog credential for use with an external data source.
    parameters:
        - name: --credential-name
          type: string
          short-summary: 'The name of the credential.'
        - name: --database-name
          type: string
          short-summary: 'The name of the database in which to create the credential.'
        - name: --user-name
          type: string
          short-summary: 'The user name that will be used when authenticating with this credential.'
"""

helps['dla catalog credential update'] = """
    type: command
    short-summary: Updates a catalog credential for use with an external data source.
    parameters:
        - name: --credential-name
          type: string
          short-summary: 'The name of the credential to update.'
        - name: --database-name
          type: string
          short-summary: 'The name of the database in which the credential exists.'
        - name: --user-name
          type: string
          short-summary: "The user name associated with the credential that will have its password updated."
"""

helps['dla catalog credential show'] = """
    type: command
    short-summary: Retrieves a catalog credential.
"""

helps['dla catalog credential list'] = """
    type: command
    short-summary: Lists catalog credentials.
"""

helps['dla catalog credential delete'] = """
    type: command
    short-summary: Deletes a catalog credential.
"""

helps['dla catalog package'] = """
    type: group
    short-summary: Manage Data Lake Analytics catalog packages.
    long-summary: These commands are in preview.
"""

helps['dla account'] = """
    type: group
    short-summary: Manage Data Lake Analytics accounts.
    long-summary: These commands are in preview.
"""

helps['dla account create'] = """
    type: command
    short-summary: Creates a Data Lake Analytics account.
    parameters:
        - name: --default-data-lake-store
          type: string
          short-summary: 'The default Data Lake Store account to associate with the created account.'
        - name: --max-degree-of-parallelism
          type: int
          short-summary: 'The maximum degree of parallelism for this account.'
        - name: --max-job-count
          type: int
          short-summary: 'The maximum number of concurrent jobs for this account.'
        - name: --query-store-retention
          type: int
          short-summary: 'The number of days to retain job metadata.'
"""

helps['dla account update'] = """
    type: command
    short-summary: Updates a Data Lake Analytics account.
    parameters:
        - name: --max-degree-of-parallelism
          type: int
          short-summary: 'The maximum degree of parallelism for this account.'
        - name: --max-job-count
          type: int
          short-summary: 'The maximum number of concurrent jobs for this account.'
        - name: --query-store-retention
          type: int
          short-summary: 'The number of days to retain job metadata.'
        - name: --firewall-state
          type: string
          short-summary: 'Enable or disable existing firewall rules.'
        - name: --allow-azure-ips
          type: string
          short-summary: 'Allow or block Azure originating IPs through the firewall.'
"""

helps['dla account show'] = """
    type: command
    short-summary: Retrieves a Data Lake Analytics account.
"""

helps['dla account list'] = """
    type: command
    short-summary: Lists Data Lake Analytics accounts in a subscription or a resource group.
"""

helps['dla account delete'] = """
    type: command
    short-summary: Deletes a Data Lake Analytics account.
"""

helps['dla account blob-storage'] = """
    type: group
    short-summary: Manage Data Lake Analytics account linked Azure Storage.
    long-summary: These commands are in preview.
"""

helps['dla account data-lake-store'] = """
    type: group
    short-summary: Manage Data Lake Analytics account linked Data Lake Store accounts.
    long-summary: These commands are in preview.
"""

helps['dla account firewall'] = """
    type: group
    short-summary: Manage Data Lake Analytics account firewall rules.
    long-summary: These commands are in preview.
"""

helps['dla account firewall create'] = """
    type: command
    short-summary: Creates a firewall rule in a Data Lake Analytics account.
    parameters:
        - name: --end-ip-address
          type: string
          short-summary: 'The end of the valid IP range for the firewall rule.'
        - name: --start-ip-address
          type: string
          short-summary: 'The start of the valid IP range for the firewall rule.'
        - name: --firewall-rule-name
          type: string
          short-summary: 'The name of the firewall rule.'
"""

helps['dla account firewall update'] = """
    type: command
    short-summary: Updates a firewall rule in a Data Lake Analytics account.
"""

helps['dla account firewall show'] = """
    type: command
    short-summary: Retrieves a firewall rule in a Data Lake Analytics account.
"""

helps['dla account firewall list'] = """
    type: command
    short-summary: Lists firewall rules in a Data Lake Analytics account.
"""

helps['dla account firewall delete'] = """
    type: command
    short-summary: Deletes a firewall rule in a Data Lake Analytics account.
"""

helps['dla account compute-policy'] = """
    type: group
    short-summary: Manage Data Lake Analytics account compute policies.
    long-summary: These commands are in preview.
"""

helps['dla account compute-policy create'] = """
    type: command
    short-summary: Creates a compute policy in the Data Lake Analytics account.
    parameters:
        - name: --max-dop-per-job
          type: int
          short-summary: 'The maximum degree of parallelism allowed per job for this policy. At least one of --min-priority-per-job and --max-dop-per-job must be specified.'
        - name: --min-priority-per-job
          type: int
          short-summary: 'The minimum priority allowed per job for this policy. At least one of --min-priority-per-job and --max-dop-per-job must be specified.'
        - name: --compute-policy-name
          type: string
          short-summary: 'The name of the compute policy to create.'
        - name: --object-id
          type: string
          short-summary: 'The Azure Active Directory object ID of the user, group or service principal to apply the policy to.'
        - name: --object-type
          type: string
          short-summary: 'The Azure Active Directory object type associated with the supplied object id.'
"""

helps['dla account compute-policy update'] = """
    type: command
    short-summary: Updates a compute policy in the Data Lake Analytics account.
    parameters:
        - name: --max-dop-per-job
          type: int
          short-summary: 'The maximum degree of parallelism allowed per job for this policy. At least one of --min-priority-per-job and --max-dop-per-job must be specified.'
        - name: --min-priority-per-job
          type: int
          short-summary: 'The minimum priority allowed per job for this policy. At least one of --min-priority-per-job and --max-dop-per-job must be specified.'
        - name: --compute-policy-name
          type: string
          short-summary: 'The name of the compute policy to update.'
"""

helps['dla account compute-policy show'] = """
    type: command
    short-summary: Retrieves a compute policy in a Data Lake Analytics account.
"""

helps['dla account compute-policy list'] = """
    type: command
    short-summary: Lists compute policies in the a Lake Analytics account.
"""

helps['dla account compute-policy delete'] = """
    type: command
    short-summary: Deletes a compute policy in a Data Lake Analytics account.
"""

helps['dla job pipeline'] = """
    type: group
    short-summary: Manage Data Lake Analytics job pipelines.
    long-summary: These commands are in preview.
"""

helps['dla job pipeline show'] = """
    type: command
    short-summary: Retrieves a job pipeline in a Data Lake Analytics account.
"""

helps['dla job pipeline list'] = """
    type: command
    short-summary: Lists job pipelines in a Data Lake Analytics account.
"""

helps['dla job recurrence'] = """
    type: group
    short-summary: Manage Data Lake Analytics job recurrences.
    long-summary: These commands are in preview.
"""

helps['dla job recurrence show'] = """
    type: command
    short-summary: Retrieves a job recurrence in a Data Lake Analytics account.
"""

helps['dla job recurrence list'] = """
    type: command
    short-summary: Lists job recurrences in a Data Lake Analytics account.
"""
