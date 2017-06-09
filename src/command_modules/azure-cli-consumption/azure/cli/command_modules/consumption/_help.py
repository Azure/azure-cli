# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['consumption'] = """
    type: group
    short-summary: Manage Azure Consumption.
"""

helps['consumption usage list'] = """
    type: command
    short-summary: List usage details
    long-summary: List usage details of the subscription, in the scope of an invoice or a billing period.
"""
