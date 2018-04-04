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
    short-summary: (DEPRECATED) Import data into Redis cache.
    long-summary: |
        WARNING: This command is deprecated. Instead, use the `import` command.
"""

helps['redis update'] = """
    type: command
    short-summary: Scale or update settings of a Redis cache.
"""

helps['redis patch-schedule'] = """
    type: group
    short-summary: Manage Redis patch schedules.
"""

helps['redis firewall-rules'] = """
    type: group
    short-summary: Manage Redis firewall rules.
"""

helps['redis linked-server'] = """
    type: group
    short-summary: Manage Redis linked servers.
"""

helps['redis linked-server set'] = """
    type: command
    short-summary: Adds a linked server to the Redis cache (requires Premium SKU).
"""
