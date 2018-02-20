# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['consumption'] = """
    type: group
    short-summary: Manage consumption of Azure resources.
"""

helps['consumption reservations'] = """
    type: group
    short-summary: Manage reservations for Azure resources.
"""

helps['consumption reservations summaries'] = """
    type: group
    short-summary: List reservations summaries.
"""
helps['consumption reservations summaries list'] = """
    type: command
    short-summary: List reservations summaries for daily or monthly by reservation order Id and optionally by reservation id.
"""

helps['consumption reservations details'] = """
    type: group
    short-summary: List reservations details.
"""

helps['consumption reservations details list'] = """
    type: command
    short-summary: List reservations details by reservation order id and optionally by reservation id
"""

helps['consumption usage'] = """
    type: group
    short-summary: Inspect the usage of Azure resources.
"""

helps['consumption usage list'] = """
    type: command
    short-summary: Show the details of Azure resource consumption, either as an invoice or within a billing period.
"""

helps['consumption pricesheet'] = """
    type: group
    short-summary: Inspect the price sheet by Azure subscription within current or specified billing period.
"""

helps['consumption pricesheet show'] = """
    type: command
    short-summary: Show the price sheet for Azure subscription within a current billing period or specified billing period
"""

helps['consumption marketplace'] = """
    type: group
    short-summary: Inspect the marketplace by Azure subscription within current or specified billing period.
"""

helps['consumption marketplace list'] = """
    type: command
    short-summary: Show the marketplace for Azure subscription within a current billing period or specified billing period
"""

helps['consumption budget'] = """
    type: group
    short-summary: Offers ability to create, get, update, and delete budgets for Azure subscription optionally by resource group name
"""

helps['consumption budget list'] = """
    type: command
    short-summary: Offers ability to create, get, update, and delete budgets for Azure subscription optionally by resource group name
"""

helps['consumption budget show'] = """
    type: command
    short-summary: Show budget for Azure subscription by budget name and, optionally by, resource group name
"""

helps['consumption budget create'] = """
    type: command
    short-summary: Create budget for Azure subscription and associate with resource group name
"""

helps['consumption budget update'] = """
    type: command
    short-summary: Update budget for Azure subscription and associate with resource group name
"""
helps['consumption budget delete'] = """
    type: command
    short-summary: Delete budget for Azure subscription optionally by resource group name
"""