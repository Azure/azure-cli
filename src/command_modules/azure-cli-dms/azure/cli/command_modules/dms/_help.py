# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['dms'] = """
    type: group
    short-summary: Manage Azure Data Migration Service (DMS) instances.
"""

helps['dms check-name-availability'] = """
    type: command
    short-summary: Check if a given DMS instance name is available in a given region as well as the name's validity.
    parameters:
        - name: --name -n
          type: string
          short-summary: >
            The Service name you wish to check.
"""

helps['dms create'] = """
    type: command
    short-summary: Create an instance of the Data Migration Service.
    parameters:
        - name: --sku-name
          type: string
          short-summary: >
            The name of the CPU SKU on which the service's Virtual Machine will run.
        - name: --subnet
          type: string
          short-summary: >
            The Resource ID of the VNet's Subnet you will use to connect the source and target DBs.
            Use "az network vnet subnet show -h" for help to get your subnet's ID.
    examples:
        - name: Create an instance of DMS.
          text: >
            az dms create -l westus -n mydms -g myresourcegroup --sku-name Basic_2vCores --subnet /subscriptions/{vnet subscription id}/resourceGroups/{vnet resource group}/providers/Microsoft.Network/virtualNetworks/{vnet name}/subnets/{subnet name}
"""

helps['dms delete'] = """
    type: command
    short-summary: Delete an instance of the Data Migration Service.
    parameters:
        - name: --delete-running-tasks
          type: bool
          short-summary: >
            Delete the resource even if it contains running tasks.
"""

helps['dms list'] = """
    type: command
    short-summary: List the DMS instances within your currently configured subscription (to set this use 'az account set'). If provided, only show the instances within a given resource group.
    parameters:
        - name: --resource-group-name -g
          type: string
          short-summary: >
            The name of the resource group the list of DMS instances should be limited to.
    examples:
        - name: List all the instances in your subscription.
          text: >
            az dms list
        - name: List all the instances in a given resource group.
          text: >
            az dms list -g myresourcegroup
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

helps['dms task'] = """
    type: group
    short-summary: Manage Tasks for a DMS Project.
"""