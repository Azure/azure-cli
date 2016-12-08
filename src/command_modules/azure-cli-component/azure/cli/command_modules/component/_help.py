# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['component'] = """
    type: group
    short-summary: Commands to manage and update Azure CLI 2.0 (Preview) components
"""

helps['component list'] = """
    type: command
    short-summary: List the installed components of Azure CLI 2.0 (Preview)
"""

helps['component remove'] = """
    type: command
    short-summary: Remove a component from Azure CLI 2.0 (Preview)
"""

helps['component update'] = """
    type: command
    short-summary: Update Azure CLI 2.0 (Preview) and all of the installed components
"""
