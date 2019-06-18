# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['consumption'] = """
    type: group
    short-summary: Manage consumption of Azure resources.
"""

helps['consumption reservation'] = """
    type: group
    short-summary: Manage reservations for Azure resources.
"""

helps['consumption reservation summary'] = """
    type: group
    short-summary: List reservation summaries.
"""
helps['consumption reservation summary list'] = """
    type: command
    short-summary: List reservation summaries for daily or monthly by order Id or reservation id.
"""

helps['consumption reservation detail'] = """
    type: group
    short-summary: List reservation details.
"""

helps['consumption reservation detail list'] = """
    type: command
    short-summary: List the details of a reservation by order id or reservation id.
"""

helps['consumption usage'] = """
    type: group
    short-summary: Inspect the usage of Azure resources.
"""

helps['consumption usage list'] = """
    type: command
    short-summary: List the details of Azure resource consumption, either as an invoice or within a billing period.
"""

helps['consumption pricesheet'] = """
    type: group
    short-summary: Inspect the price sheet of an Azure subscription within a billing period.
"""

helps['consumption pricesheet show'] = """
    type: command
    short-summary: Show the price sheet for an Azure subscription within a billing period.
"""

helps['consumption marketplace'] = """
    type: group
    short-summary: Inspect the marketplace usage data of an Azure subscription within a billing period.
"""

helps['consumption marketplace list'] = """
    type: command
    short-summary: List the marketplace for an Azure subscription within a billing period.
"""

helps['consumption budget'] = """
    type: group
    short-summary: Manage budgets for an Azure subscription.
"""

helps['consumption budget list'] = """
    type: command
    short-summary: List budgets for an Azure subscription.
"""

helps['consumption budget show'] = """
    type: command
    short-summary: Show budget for an Azure subscription.
"""

helps['consumption budget create'] = """
    type: command
    short-summary: Create a budget for an Azure subscription.
"""

helps['consumption budget delete'] = """
    type: command
    short-summary: Delete a budget for an Azure subscription.
"""
