# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['redis'] = """
    type: group
    short-summary: Access to a secure, dedicated Redis cache for your Azure applications.
"""

helps['redis export'] = """
    type: command
    short-summary: Export data stored in a Redis cache.
"""

helps['redis import-method'] = """
    type: command
    short-summary: Import data into a Redis cache.
"""

helps['redis update-settings'] = """
    type: command
    short-summary: (DEPRECATED) Update the settings of a Redis cache.
    long-summary: |
        WARNING: This command is deprecated. Instead, use the `update` command.
"""

helps['redis update'] = """
    type: command
    short-summary: Scale or update settings of a Redis cache.
"""

helps['redis patch-schedule'] = """
    type: group
    short-summary: Manage Redis patch schedules.
"""
