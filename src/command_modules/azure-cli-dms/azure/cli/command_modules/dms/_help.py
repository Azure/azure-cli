# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from knack.help_files import helps


helps['dms'] = """
    type: group
    short-summary: Manage Azure Data Migration Service (DMS) instances.
"""

helps['dms check-name'] = """
    type: command
    short-summary: Check if a given DMS instance name is available in a given region as well as the name's validity.
    parameters:
        - name: --name -n
          type: string
          short-summary: >
            The Service name to check.
"""

helps['dms check-status'] = """
    type: command
    short-summary: Perform a health check and return the status of the service and virtual machine size.
"""

helps['dms create'] = """
    type: command
    short-summary: Create an instance of the Data Migration Service.
    parameters:
        - name: --sku-name
          type: string
          short-summary: >
            The name of the CPU SKU on which the service's Virtual Machine will run. Check the name and the availability of SKUs in your area with "az dms list-skus".
        - name: --subnet
          type: string
          short-summary: >
            The Resource ID of the VNet's Subnet you will use to connect the source and target DBs.
            Use "az network vnet subnet show -h" for help to get your subnet's ID.
    examples:
        - name: Create an instance of DMS.
          text: >
            az dms create -l westus -n mydms -g myresourcegroup --sku-name Basic_2vCores --subnet /subscriptions/{vnet subscription id}/resourceGroups/{vnet resource group}/providers/Microsoft.Network/virtualNetworks/{vnet name}/subnets/{subnet name} --tags tagName1=tagValue1 tagWithNoValue
"""

helps['dms delete'] = """
    type: command
    short-summary: Delete an instance of the Data Migration Service.
    parameters:
        - name: --delete-running-tasks
          type: bool
          short-summary: >
            Cancel any running tasks before deleting the service.
"""

helps['dms list'] = """
    type: command
    short-summary: List the DMS instances within your currently configured subscription (to set this use "az account set"). If provided, only show the instances within a given resource group.
    examples:
        - name: List all the instances in your subscription.
          text: >
            az dms list
        - name: List all the instances in a given resource group.
          text: >
            az dms list -g myresourcegroup
"""

helps['dms list-skus'] = """
    type: command
    short-summary: List the SKUs that are supported by the Data Migration Service.
"""

helps['dms show'] = """
    type: command
    short-summary: Show the details for an instance of the Data Migration Service.
"""

helps['dms start'] = """
    type: command
    short-summary: Start an instance of the Data Migration Service. It can then be used to run data migrations.
"""

helps['dms stop'] = """
    type: command
    short-summary: Stop an instance of the Data Migration Service. While stopped, it can't be used to run data migrations and the owner won't be billed.
"""

helps['dms wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the DMS instance is met.
"""

helps['dms project'] = """
    type: group
    short-summary: Manage Projects for an instance of the Data Migration Service.
"""

helps['dms project create'] = """
    type: command
    short-summary: Create a migration Project which can contain multiple Tasks.
    parameters:
        - name: --source-platform
          type: string
          short-summary: >
            The type of server for the source database. The supported types are: SQL.
        - name: --target-platform
          type: string
          short-summary: >
            The type of service for the target database. The supported types are: SQLDB.
    examples:
        - name: Create a Project for a DMS instance.
          text: >
            az dms project create -l westus -n myproject -g myresourcegroup --service-name mydms --source-platform SQL --target-platform SQLDB --tags tagName1=tagValue1 tagWithNoValue
"""

helps['dms project delete'] = """
    type: command
    short-summary: Delete a Project.
    parameters:
        - name: --delete-running-tasks
          type: bool
          short-summary: >
            Cancel any running tasks before deleting the Project.
"""

helps['dms project list'] = """
    type: command
    short-summary: List the Projects within an instance of DMS.
"""

helps['dms project show'] = """
    type: command
    short-summary: Show the details of a migration Project.
"""

helps['dms project check-name'] = """
    type: command
    short-summary: Check if a given Project name is available within a given instance of DMS as well as the name's validity.
    parameters:
        - name: --name -n
          type: string
          short-summary: >
            The Project name to check.
"""

helps['dms project task'] = """
    type: group
    short-summary: Manage Tasks for a Data Migration Service instance's Project.
"""

helps['dms project task create'] = r"""
    type: command
    short-summary: Create and start a migration Task.
    parameters:
        - name: --database-options-json
          type: string
          short-summary: >
            Database and table information. This can be either a JSON-formatted string or the location to a file containing the JSON object. See example below for the format.
        - name: --source-connection-json
          type: string
          short-summary: >
            The connection information to the source server. This can be either a JSON-formatted string or the location to a file containing the JSON object. See example below for the format.
        - name: --target-connection-json
          type: string
          short-summary: >
            The connection information to the target server. This can be either a JSON-formatted string or the location to a file containing the JSON object. See example below for the format.
        - name: --enable-data-integrity-validation
          type: bool
          short-summary: >
            Whether to perform a checksum based data integrity validation between source and target for the selected database and tables.
        - name: --enable-query-analysis-validation
          type: bool
          short-summary: >
            Whether to perform a quick and intelligent query analysis by retrieving queries from the source database and
            executing them in the target. The result will have execution statistics for executions in source and target databases
            for the extracted queries.
        - name: --enable-schema-validation
          type: bool
          short-summary: >
            Whether to compare the schema information between source and target.
    examples:
        - name: Create and start a Task which performs no validation checks.
          text: >
            az dms project task create --database-options-json C:\CLI Files\databaseOptions.json -n mytask --project-name myproject -g myresourcegroup --service-name mydms --source-connection-json '{'dataSource': 'myserver', 'authentication': 'SqlAuthentication', 'encryptConnection': 'true', 'trustServerCertificate': 'true'}' --target-connection-json C:\CLI Files\targetConnection.json
        - name: Create and start a Task which performs all validation checks.
          text: >
            az dms project task create --database-options-json C:\CLI Files\databaseOptions.json -n mytask --project-name myproject -g myresourcegroup --service-name mydms --source-connection-json C:\CLI Files\sourceConnection.json --target-connection-json C:\CLI Files\targetConnection.json --enable-data-integrity-validation=True --enable-query-analysis-validation --enable-schema-validation
        - name: The format of the database options JSON object.
          text: >
            [
                {
                    "name": "source database",
                    "target_database_name": "target database",
                    "make_source_db_read_only": false|true,
                    "table_map": {
                        "schema.SourceTableName1": "schema.TargetTableName1",
                        "schema.SourceTableName2": "schema.TargetTableName2",
                        ...n
                    }
                },
                ...n
            ]
        - name: The format of the connection JSON object.
          text: >
            {
                "userName": "user name",    // if this is missing or null, you will be prompted
                "password": null,           // if this is missing or null (highly recommended) you will be prompted
                "dataSource": "server name[,port]",
                "authentication": "SqlAuthentication|WindowsAuthentication",
                "encryptConnection": true,      // highly recommended to leave as true
                "trustServerCertificate": true  // highly recommended to leave as true
            }
"""

helps['dms project task delete'] = """
    type: command
    short-summary: Delete a migration Task.
    parameters:
        - name: --delete-running-tasks
          type: bool
          short-summary: >
            If the Task is currently running, cancel the Task before deleting the Project.
"""

helps['dms project task list'] = """
    type: command
    short-summary: List the Tasks within a Project. Some tasks may have a status of Unknown, which indicates that an error occurred while querying the status of that task.
    parameters:
        - name: --task-type
          type: string
          short-summary: >
            Filters the list by the type of task. For the list of possible types see "az dms check-status".
    examples:
        - name: List all Tasks within a Project.
          text: >
            az dms project task list --project-name myproject -g myresourcegroup --service-name mydms
        - name: List only the SQL to SQL migration tasks within a Project.
          text: >
            az dms project task list --project-name myproject -g myresourcegroup --service-name mydms --task-type Migrate.SqlServer.SqlDb
"""

helps['dms project task show'] = """
    type: command
    short-summary: Show the details of a migration Task. Use the "--expand" to get more details.
    parameters:
        - name: --expand
          type: string
          short-summary: >
            Expand the response to provide more details. Use with "command" to see more details of the Task.
            Use with "output" to see the results of the Task's migration.
"""

helps['dms project task cancel'] = """
    type: command
    short-summary: Cancel a Task if it's currently queued or running.
"""

helps['dms project task check-name'] = """
    type: command
    short-summary: Check if a given Task name is available within a given instance of DMS as well as the name's validity.
    parameters:
        - name: --name -n
          type: string
          short-summary: >
            The Task name to check.
"""
