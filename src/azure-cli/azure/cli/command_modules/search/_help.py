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

helps['search service query-key create'] = """
type: command
short-summary: Creates a query key for a given Azure Search service.
examples:
  - name: Create a query key for a Search service.
    text: >
        az search service query-key create --resource-group MyResourceGroup --search-service-name MySearchService -n MyQueryKey
"""

helps['search service admin-key regenerate'] = """
type: command
short-summary: Regenerate an admin key for a given Azure Search service.
examples:
  - name: Regenerate the primary admin key for a Search service.
    text: >
        az search service admin-key regenerate --resource-group MyResourceGroup --search-service-name MySearchService --key-kind primary
  - name: Regenerate the secondary admin key for a Search service.
    text: >
        az search service admin-key regenerate --resource-group MyResourceGroup --search-service-name MySearchService --key-kind secondary
"""

helps['search service check-name-availability'] = """
type: command
short-summary: Check the availability of a given Azure Search service name.
examples:
  - name: Check if a Search service name is available.
    text: >
        az search service check-name-availability --name MySearchService --type searchServices
"""

helps['search service upgrade'] = """
type: command
short-summary: Upgrade a given Azure Search service.
examples:
  - name: Upgrade a Search service.
    text: >
        az search service upgrade --resource-group MyResourceGroup --search-service-name MySearchService
"""

helps['search service network-security-perimeter-configuration reconcile'] = """
type: command
short-summary: Reconcile network security perimeter configuration for a given Azure Search service.
examples:
  - name: Reconcile network security perimeter configuration and specify a perimeter name.
    text: >
        az search service network-security-perimeter-configuration reconcile --resource-group MyResourceGroup --search-service-name MySearchService --nsp-config-name MyPerimeter
"""

helps['search service shared-private-link-resource create'] = """
type: command
short-summary: Create a shared private link resource for a given Azure Search service.
examples:
  - name: Create a shared private link resource for a Search service.
    text: >
        az search service shared-private-link-resource create --resource-group MyResourceGroup --search-service-name MySearchService --name MySharedPrivateLinkResource --group-id MyGroupId --resource-id /subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/{provider}/{resourceType}/{resourceName}
  - name: Create a shared private link resource and specify a request message.
    text: >
        az search service shared-private-link-resource create --resource-group MyResourceGroup --search-service-name MySearchService --name MySharedPrivateLinkResource --group-id MyGroupId --resource-id /subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/{provider}/{resourceType}/{resourceName} --request-message "Please approve this connection."
"""

helps['search service shared-private-link-resource update'] = """
type: command
short-summary: Update a shared private link resource for a given Azure Search service.
examples:
  - name: Update the request message for a shared private link resource.
    text: >
        az search service shared-private-link-resource update --resource-group MyResourceGroup --search-service-name MySearchService --name MySharedPrivateLinkResource --request-message "Updated request message."
  - name: Approve a shared private link resource connection.
    text: >
        az search service shared-private-link-resource update --resource-group MyResourceGroup --search-service-name MySearchService --name MySharedPrivateLinkResource --status Approved
"""

helps['search service private-endpoint-connection update'] = """
type: command
short-summary: Update a private endpoint connection for a given Azure Search service.
examples:
  - name: Approve a private endpoint connection.
    text: >
        az search service private-endpoint-connection update --resource-group MyResourceGroup --search-service-name MySearchService --name MyPrivateEndpointConnection
"""
