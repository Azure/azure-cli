# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['search'] = """
type: group
short-summary: Manage Azure Search services, admin keys and query keys.
"""

helps['search admin-key'] = """
type: group
short-summary: Manage Azure Search admin keys.
"""

helps['search query-key'] = """
type: group
short-summary: Manage Azure Search query keys.
"""

helps['search service'] = """
type: group
short-summary: Manage Azure Search services.
"""

helps['search service update'] = """
type: command
short-summary: Update partition and replica of the given search service.
"""
