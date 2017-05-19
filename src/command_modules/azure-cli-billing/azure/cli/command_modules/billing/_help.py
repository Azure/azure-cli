# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['billing'] = """
    type: group
    short-summary: Manage Azure Billing.
"""

helps['billing invoice'] = """
    type: group
    short-summary: Get billing invoices of the subscription.
"""

helps['billing period'] = """
    type: group
    short-summary: Get billing periods of the subscription.
"""
