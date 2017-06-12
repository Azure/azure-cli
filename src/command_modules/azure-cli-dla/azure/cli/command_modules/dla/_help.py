# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['dla'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics accounts, jobs, and catalogs.
    long-summary: If you don't have the Data Lake Analytics component installed, add it with `az component update --add dla`. These commands are in preview.
"""

helps['dla job'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics jobs.
    long-summary: These commands are in preview.
"""

helps['dla job submit'] = """
    type: command
    short-summary: submits the job to the Data Lake Analytics account.
    parameters:
        - name: --job-name
          type: string
          short-summary: 'Job name for the job'
        - name: --script
          type: string
          short-summary: 'The script to submit'
          long-summary: This is either the script contents or use `@<file path>` to load the script from a file
        - name: --runtime-version
          short-summary: 'The runtime version to use'
          long-summary: This parameter is used for explicitly overwriting the default runtime. It should only be done if you know what you are doing.
        - name: --degree-of-parallelism
          short-summary: 'The degree of parallelism for the job'
          long-summary: Higher values equate to more parallelism and will usually yield faster running jobs, at the cost of more AUs consumed by the job.
        - name: --priority
          short-summary: 'The priority of the job'
          long-summary: Lower values increase the priority, with the lowest value being 1. This determines the order jobs are run in.

"""

helps['dla job cancel'] = """
    type: command
    short-summary: cancels the job in the Data Lake Analytics account.
"""

helps['dla job show'] = """
    type: command
    short-summary: Retrieves the job in the Data Lake Analytics account.
"""

helps['dla job wait'] = """
    type: command
    short-summary: Waits for the job in the Data Lake Analytics account to finish, returning the job once finished
    parameters:
        - name: --job-id
          type: string
          short-summary: 'Job ID for the job to poll'
"""

helps['dla job list'] = """
    type: command
    short-summary: lists jobs in the Data Lake Analytics account.
"""

helps['dla catalog'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalogs.
    long-summary: These commands are in preview.
"""

helps['dla catalog database'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog databases.
    long-summary: These commands are in preview.
"""

helps['dla catalog assembly'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog assemblies.
    long-summary: These commands are in preview.
"""

helps['dla catalog external-data-source'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog external data sources.
    long-summary: These commands are in preview.
"""

helps['dla catalog procedure'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog stored procedures.
    long-summary: These commands are in preview.
"""

helps['dla catalog schema'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog schemas.
    long-summary: These commands are in preview.
"""

helps['dla catalog table'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog tables.
    long-summary: These commands are in preview.
"""

helps['dla catalog table list'] = """
    type: command
    short-summary: Lists all tables in the database or in the database and schema combination
    parameters:
        - name: --database-name
          type: string
          short-summary: 'The name of the database to list tables for'
        - name: --schema-name
          type: string
          short-summary: 'The name of the schema in the database to list tables for.'
"""

helps['dla catalog table-partition'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog table partitions.
    long-summary: These commands are in preview.
"""

helps['dla catalog table-stats'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog table statistics.
    long-summary: These commands are in preview.
"""

helps['dla catalog table-stats list'] = """
    type: command
    short-summary: Lists all table statistics in the database or in the database and schema or in a specific table
    parameters:
        - name: --database-name
          type: string
          short-summary: 'The name of the database to list table statitics for'
        - name: --schema-name
          type: string
          short-summary: 'The name of the schema in the database to list table statistics for.'
        - name: --table-name
          type: string
          short-summary: 'The name of the table to list statistics in. --schema-name must also be specified for this parameter to be honored'
"""

helps['dla catalog table-type'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog table types.
    long-summary: These commands are in preview.
"""

helps['dla catalog tvf'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog table valued functions, or TVFs.
    long-summary: These commands are in preview.
"""

helps['dla catalog tvf list'] = """
    type: command
    short-summary: Lists all table valued functions in the database or in the database and schema combination
    parameters:
        - name: --database-name
          type: string
          short-summary: 'The name of the database to list table valued functions for'
        - name: --schema-name
          type: string
          short-summary: 'The name of the schema in the database to list table valued functions for.'
"""

helps['dla catalog view'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog views.
    long-summary: These commands are in preview.
"""

helps['dla catalog view list'] = """
    type: command
    short-summary: Lists all views in the database or in the database and schema combination
    parameters:
        - name: --database-name
          type: string
          short-summary: 'The name of the database to list views for'
        - name: --schema-name
          type: string
          short-summary: 'The name of the schema in the database to list views for.'
"""

helps['dla catalog credential'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog credentials.
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
          short-summary: 'The user name that will be used when authenticating with this credential'
"""

helps['dla catalog credential update'] = """
    type: command
    short-summary: Updates the catalog credential for use with an external data source.
    parameters:
        - name: --credential-name
          type: string
          short-summary: 'The name of the credential to update.'
        - name: --database-name
          type: string
          short-summary: 'The name of the database in which the credential exists.'
        - name: --user-name
          type: string
          short-summary: "The user name associated with the credential that will have it's password updated."
"""

helps['dla catalog credential show'] = """
    type: command
    short-summary: Retrieves the catalog credential.
"""

helps['dla catalog credential list'] = """
    type: command
    short-summary: Lists the catalog credentials.
"""

helps['dla catalog credential delete'] = """
    type: command
    short-summary: deletes the catalog credential.
"""

helps['dla catalog package'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog packages.
    long-summary: These commands are in preview.
"""

helps['dla account'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics accounts.
    long-summary: These commands are in preview.
"""

helps['dla account create'] = """
    type: command
    short-summary: Creates a Data Lake Analytics account.
    parameters:
        - name: --default-data-lake-store
          type: string
          short-summary: 'The default Data Lake Store account to associate with the Data Lake Analytics account being created'
        - name: --max-degree-of-parallelism
          type: int
          short-summary: 'The maximum supported degree of parallelism for this account.'
        - name: --max-job-count
          type: int
          short-summary: 'The maximum supported jobs running under the account at the same time.'
        - name: --query-store-retention
          type: int
          short-summary: 'The number of days that job metadata is retained.'
"""

helps['dla account update'] = """
    type: command
    short-summary: Updates a Data Lake Analytics account.
    parameters:
        - name: --max-degree-of-parallelism
          type: int
          short-summary: 'The maximum supported degree of parallelism for this account.'
        - name: --max-job-count
          type: int
          short-summary: 'The maximum supported jobs running under the account at the same time.'
        - name: --query-store-retention
          type: int
          short-summary: 'Optionally enable/disable existing firewall rules.'
        - name: --firewall-state
          type: string
          short-summary: 'The number of days that job metadata is retained.'
        - name: --allow-azure-ips
          type: string
          short-summary: 'Optionally allow/block Azure originating IPs through the firewall.'
"""

helps['dla account show'] = """
    type: command
    short-summary: Retrieves the Data Lake Analytics account.
"""

helps['dla account list'] = """
    type: command
    short-summary: Lists Data Lake Analytics accounts in a subscription or a specific resource group.
"""

helps['dla account delete'] = """
    type: command
    short-summary: Deletes the Data Lake Analytics account.
"""

helps['dla account blob-storage'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics account linked Azure Storage.
    long-summary: These commands are in preview.
"""

helps['dla account data-lake-store'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics account linked Data Lake Store accounts.
    long-summary: These commands are in preview.
"""

helps['dla account firewall'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics account firewall rules.
    long-summary: These commands are in preview.
"""

helps['dla account firewall create'] = """
    type: command
    short-summary: Creates a firewall rule in the Data Lake Analytics account.
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
    short-summary: Updates a firewall rule in the Data Lake Analytics account.
"""

helps['dla account firewall show'] = """
    type: command
    short-summary: Retrieves a firewall rule in the Data Lake Analytics account.
"""

helps['dla account firewall list'] = """
    type: command
    short-summary: Lists firewall rules in the Data Lake Analytics account.
"""

helps['dla account firewall delete'] = """
    type: command
    short-summary: Deletes a firewall rule in the Data Lake Analytics account.
"""
