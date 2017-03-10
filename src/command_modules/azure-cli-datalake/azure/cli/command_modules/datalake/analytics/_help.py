# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long
helps['datalake'] = """
    type: group
    short-summary: Access to Data Lake Store and Analytics management
    long-summary: If you don't have the datalake component installed, add it with `az component update --add datalake`
"""

helps['datalake analytics'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics accounts, jobs and catalogs. 
"""

helps['datalake analytics job'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics jobs. 
"""

helps['datalake analytics job submit'] = """
    type: command
    short-summary: submits the job to the Data Lake analytics account. 
    parameters:
        - name: --job-name
          type: string
          short-summary: 'Job name for the job'
        - name: --script
          type: string
          short-summary: 'The script to submit'
          long-summary: This can be either the script contents or a valid file path to a file containing the script
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

helps['datalake analytics job cancel'] = """
    type: command
    short-summary: cancels the job in the Data Lake analytics account. 
"""

helps['datalake analytics job show'] = """
    type: command
    short-summary: Retrieves the job in the Data Lake analytics account. 
"""

helps['datalake analytics job wait'] = """
    type: command
    short-summary: Waits for the job in the Data Lake analytics account to finish, returning the job once finished
    parameters:
        - name: --job-id
          type: string
          short-summary: 'Job ID for the job to poll'
"""

helps['datalake analytics job list'] = """
    type: command
    short-summary: lists jobs in the Data Lake analytics account. 
"""

helps['datalake analytics catalog'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalogs. 
"""

helps['datalake analytics catalog database'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog databases. 
"""

helps['datalake analytics catalog assembly'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog assemblies. 
"""

helps['datalake analytics catalog externaldatasource'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog external data sources. 
"""

helps['datalake analytics catalog procedure'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog stored procedures. 
"""

helps['datalake analytics catalog schema'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog schemas. 
"""

helps['datalake analytics catalog table'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog tables. 
"""

helps['datalake analytics catalog tablepartition'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog table partitions. 
"""

helps['datalake analytics catalog tablestats'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog table statistics. 
"""

helps['datalake analytics catalog tabletype'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog table types. 
"""

helps['datalake analytics catalog tablevaluedfunction'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog table valued functions, or TVFs. 
"""

helps['datalake analytics catalog view'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog views. 
"""

helps['datalake analytics catalog credential'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics catalog credentials. 
"""

helps['datalake analytics catalog credential create'] = """
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

helps['datalake analytics catalog credential update'] = """
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

helps['datalake analytics catalog credential show'] = """
    type: command
    short-summary: Retrieves the catalog credential. 
"""

helps['datalake analytics catalog credential list'] = """
    type: command
    short-summary: Lists the catalog credentials. 
"""

helps['datalake analytics catalog credential delete'] = """
    type: command
    short-summary: deletes the catalog credential. 
"""

helps['datalake analytics account'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics accounts. 
"""

helps['datalake analytics account create'] = """
    type: command
    short-summary: Creates a Data Lake Analytics account. 
    parameters:
        - name: --default-datalake-store
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

helps['datalake analytics account update'] = """
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

helps['datalake analytics account show'] = """
    type: command
    short-summary: Retrieves the Data Lake Analytics account. 
"""

helps['datalake analytics account list'] = """
    type: command
    short-summary: Lists Data Lake Analytics accounts in a subscription or a specific resource group.
"""

helps['datalake analytics account delete'] = """
    type: command
    short-summary: Deletes the Data Lake Analytics account. 
"""

helps['datalake analytics account blob'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics account linked Azure Storage. 
"""

helps['datalake analytics account datalake-store'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics account linked Data Lake Store accounts. 
"""

helps['datalake analytics account firewall'] = """
    type: group
    short-summary: Commands to manage Data Lake Analytics account firewall rules. 
"""

helps['datalake analytics account firewall create'] = """
    type: command
    short-summary: Creates a firewall rule in the Data Lake Analytics account.
    parameters:
        - name: --end-ip-address
          type: string
          short-summary: 'The end of the valid ip range for the firewall rule.'
        - name: --start-ip-address
          type: string
          short-summary: 'The start of the valid ip range for the firewall rule.'
        - name: --firewall-rule-name
          type: string
          short-summary: 'The name of the firewall rule.'
"""

helps['datalake analytics account firewall update'] = """
    type: command
    short-summary: Updates a firewall rule in the Data Lake Analytics account. 
"""

helps['datalake analytics account firewall show'] = """
    type: command
    short-summary: Retrieves a firewall rule in the Data Lake Analytics account. 
"""

helps['datalake analytics account firewall list'] = """
    type: command
    short-summary: Lists firewall rules in the Data Lake Analytics account. 
"""

helps['datalake analytics account firewall delete'] = """
    type: command
    short-summary: Deletes a firewall rule in the Data Lake Analytics account. 
"""