# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps  # pylint: disable=unused-import

# pylint: disable=line-too-long

helps['cloud'] = """
    type: group
    short-summary: Manage the Azure clouds registered
"""

helps['cloud list'] = """
            type: command
            short-summary: List the clouds registered
"""

helps['cloud show'] = """
            type: command
            short-summary: Show the configuration for a registered cloud
"""

helps['cloud register'] = """
            type: command
            short-summary: Register a cloud
"""

helps['cloud unregister'] = """
            type: command
            short-summary: Unregister a cloud
"""

helps['cloud set'] = """
            type: command
            short-summary: Set the active cloud
"""

helps['cloud update'] = """
            type: command
            short-summary: Update the configuration for a cloud
"""
