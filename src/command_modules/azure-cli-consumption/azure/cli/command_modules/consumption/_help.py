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
