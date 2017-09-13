# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['extension'] = """
    type: group
    short-summary: Manage and update CLI extensions.
"""

helps['extension add'] = """
    type: command
    short-summary: Add an extension.
"""

helps['extension list'] = """
    type: command
    short-summary: List the installed extensions.
"""

helps['extension list-available'] = """
    type: command
    short-summary: List publicly available extensions.
"""

helps['extension show'] = """
    type: command
    short-summary: Show an extension.
"""

helps['extension remove'] = """
    type: command
    short-summary: Remove an extension.
"""
