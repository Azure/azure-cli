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
    short-summary: Manage reservations summaries for daily or monthly.
"""

helps['consumption reservations details'] = """
    type: group
    short-summary: Manage reservations details.
"""

helps['consumption usage'] = """
    type: group
    short-summary: Inspect the usage of Azure resources.
"""

helps['consumption usage list'] = """
    type: command
    short-summary: Show the details of Azure resource consumption, either as an invoice or within a billing period.
"""
