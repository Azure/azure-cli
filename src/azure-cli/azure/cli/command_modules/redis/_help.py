# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['redis'] = """
type: group
short-summary: Manage dedicated Redis caches for your Azure applications.
"""

helps['redis export'] = """
type: command
short-summary: Export data stored in a Redis cache.
"""

helps['redis firewall-rules'] = """
type: group
short-summary: Manage Redis firewall rules.
"""

helps['redis firewall-rules update'] = """
type: command
short-summary: Update a redis cache firewall rule.
"""

helps['redis import'] = """
type: command
short-summary: Import data into a Redis cache.
"""

helps['redis list'] = """
type: command
short-summary: List Redis Caches.
long-summary: Lists details about all caches within current Subscription or provided Resource Group.
"""

helps['redis patch-schedule'] = """
type: group
short-summary: Manage Redis patch schedules.
"""

helps['redis patch-schedule update'] = """
type: command
short-summary: Update the patching schedule for Redis cache.
long-summary: Usage example - az redis patch-schedule update --name testCacheName --resource-group testResourceGroup --schedule-entries '[{"dayOfWeek":"Tuesday","startHourUtc":"00","maintenanceWindow":"PT5H"}]'
"""

helps['redis server-link'] = """
type: group
short-summary: Manage Redis server links.
"""

helps['redis update'] = """
type: command
short-summary: Update a Redis cache.
long-summary: Scale or update settings of a Redis cache.
"""
