# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['cloud'] = """
    type: group
    short-summary: Manage registered Azure clouds.
"""

helps['cloud list'] = """
            type: command
            short-summary: List registered clouds.
"""

helps['cloud show'] = """
            type: command
            short-summary: Get the details of a registered cloud.
"""

helps['cloud register'] = """
    type: command
    short-summary: Register a cloud.
    long-summary: When registering a cloud, specify only the resource manager endpoint for the autodetection of other endpoints.
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
            short-summary: Update the configuration of a cloud.
"""

helps['cloud list-profiles'] = """
            type: command
            short-summary: List the supported profiles for a cloud.
"""
