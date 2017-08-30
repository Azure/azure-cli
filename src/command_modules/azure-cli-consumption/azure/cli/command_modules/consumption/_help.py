# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['consumption'] = """
    type: group
    short-summary: Manage consumption of Azure resources.
"""

helps['consumption usage'] = """
    type: group
    short-summary: Inspect consumption usage.
"""

helps['consumption usage list'] = """
    type: command
    short-summary: List consumption usage details.
    long-summary: List usage details of the subscription, as an invoice or within a billing period.
"""
