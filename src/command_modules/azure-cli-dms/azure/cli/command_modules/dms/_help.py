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
    short-summary: List the DMS instances within your currently configured subscription (to set this use 'az account set'). If provided, only show the instances within a given resource group.
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
    short-summary: Retrieve details for an instance of the Data Migration Service.
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
        - name: --source-connection-json
          type: string
          short-summary: >
            Either a JSON-formatted string or the location to a file containing the JSON object. See example below for the format.
        - name: --source-platform
          type: string
          short-summary: >
            The type of server for the source database. The supported types are: SQL.
        - name: --target-connection-json
          type: string
          short-summary: >
            Either a JSON-formatted string or the location to a file containing the JSON object. See example below for the format.
        - name: --target-platform
          type: string
          short-summary: >
            The type of service for the target database. The supported types are: SQLDB.
    examples:
        - name: Create a Project for a DMS instance. Notice the second tag doesn't have a value.
          text: >
            az dms project create -g myresourcegroup --service-name mydms -l westus -n myproject --source-connection-json C:\CLI Files\sourceConnection.json --source-platform SQL --target-connection-json C:\CLI Files\targetConnection.json --target-platform SQLDB --database-list SourceDatabase1 SourceDatabase2 --tags Type=test CLI
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

helps['dms task'] = """
    type: group
    short-summary: Manage Tasks for a Data Migration Service instance's Project.
"""