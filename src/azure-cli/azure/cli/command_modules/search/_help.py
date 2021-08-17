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

helps['search private-endpoint-connection'] = """
type: group
short-summary: Manage Azure Search private endpoint connections.
"""

helps['search private-link-resource'] = """
type: group
short-summary: Manage Azure Search private link resources.
"""

helps['search shared-private-link-resource'] = """
type: group
short-summary: Manage Azure Search shared private link resources.
"""

helps['search shared-private-link-resource wait'] = """
type: command
short-summary: Wait for async shared private link resource operations.
"""

helps['search service create'] = """
type: command
short-summary: Creates a Search service in the given resource group.
parameters:
  - name: --sku
    short-summary: 'The SKU of the search service, which determines price tier and capacity limits. Accepted Values: Free, Basic, Standard, Standard2, Standard3'
"""

helps['search service update'] = """
type: command
short-summary: Update partition and replica of the given search service.
"""

helps['search service wait'] = """
type: command
short-summary: Wait for async service operations.
"""
