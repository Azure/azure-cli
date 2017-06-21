# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps  # pylint: disable=unused-import


helps['cloud'] = """
    type: group
    short-summary: Manage the registered Azure clouds.
"""

helps['cloud list'] = """
            type: command
            short-summary: List the registered clouds.
"""

helps['cloud show'] = """
            type: command
            short-summary: Show the configuration of a registered cloud.
"""

helps['cloud register'] = """
            type: command
            short-summary: Register a cloud.
"""

helps['cloud unregister'] = """
            type: command
            short-summary: Unregister a cloud.
"""

helps['cloud set'] = """
            type: command
            short-summary: Set the active cloud.
"""

helps['cloud update'] = """
            type: command
            short-summary: Update the configuration for a cloud.
"""

helps['cloud list-profiles'] = """
            type: command
            short-summary: List the profiles a given cloud supports.
"""
