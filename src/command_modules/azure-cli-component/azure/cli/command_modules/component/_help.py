# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['component'] = """
    type: group
    short-summary: Manage and update Azure CLI 2.0 components.
"""

helps['component list'] = """
    type: command
    short-summary: List the installed components of Azure CLI 2.0.
"""

helps['component remove'] = """
    type: command
    short-summary: Remove a component from Azure CLI 2.0.
"""

helps['component update'] = """
    type: command
    short-summary: Update Azure CLI 2.0 and all of the installed components.
"""
