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

helps['dms check-status'] = """
    type: command
    short-summary: Check the status of a given DMS instance.
    parameters:
        - name: --name -n
          type: string
          short-summary: >
            The name of the service you wish to check.
"""

helps['dms create'] = """
    type: command
    short-summary: Create an instance of the Data Migration Service.
    parameters:
        - name: --sku-name
          type: string
          short-summary: >
            The name of the CPU SKU on which the service's Virtual Machine will run.
        - name: --virtual-subnet-id
          type: string
          short-summary: >
            The Resource ID of the VNet's Subnet you will use to connect the source and target DBs.
            Use "az network vnet subnet show -h" for help to get your subnet's ID.
    examples:
        - name: Create an instance of DMS.
          text: >
            az dms create -l westus -n mydms -g myresourcegroup --sku-name Basic_2vCores --virtual-subnet-id /subscriptions/{vnet subscription id}/resourceGroups/{vnet resource group}/providers/Microsoft.Network/virtualNetworks/{vnet name}/subnets/{subnet name}
"""

helps['dms show'] = """
    type: command
    short-summary: Get the details of a given DMS instance.
"""

helps['dms task'] = """
    type: group
    short-summary: Manage Tasks for a DMS Project.
"""