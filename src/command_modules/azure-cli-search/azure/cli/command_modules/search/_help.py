# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["search"] = """
type: group
short-summary: Manage Azure Search services, admin keys and query keys.
"""

helps["search admin-key"] = """
type: group
short-summary: Manage Azure Search admin keys.
examples:
-   name: Gets the primary and secondary admin API keys for the specified Azure Search
        service.
    text: az search admin-key show --service-name MyService --resource-group MyResourceGroup
    crafted: 'True'
"""

helps["search query-key"] = """
type: group
short-summary: Manage Azure Search query keys.
"""

helps["search service"] = """
type: group
short-summary: Manage Azure Search services.
examples:
-   name: Creates a Search service in the given resource group.
    text: az search service create --name MySearchService --sku {sku} --location westus2
        --resource-group MyResourceGroup
    crafted: 'True'
"""

helps["search service update"] = """
type: command
short-summary: Update partition and replica of the given search service.
"""

