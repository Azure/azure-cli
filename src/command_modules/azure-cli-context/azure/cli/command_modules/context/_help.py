# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['context'] = """
    type: group
    short-summary: Manage storage contexts
"""

helps['context create'] = """
    type: command
    short-summary: Create a storage context
"""

helps['context delete'] = """
    type: command
    short-summary: Delete a storage context
"""

helps['context list'] = """
    type: command
    short-summary: List all storage contexts
"""

helps['context modify'] = """
    type: command
    short-summary: Modify a storage context
"""

helps['context show'] = """
    type: command
    short-summary: Show the details of a storage context
"""

helps['context switch'] = """
    type: command
    short-summary: Switch your active storage context
"""
