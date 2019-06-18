# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)


def _get_resource_group_location(cli_ctx, resource_group_name):
    from azure.mgmt.resource import ResourceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    client = get_mgmt_service_client(cli_ctx, ResourceManagementClient)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location


def create_search_service(cmd, resource_group_name, search_service_name, sku, location=None, partition_count=0,
                          replica_count=0,):
    """
    Creates a Search service in the given resource group.

    :param resource_group_name: Name of resource group.
    :param search_service_name: Name of the search service.
    :param sku: The SKU of the search service, which determines price tier and capacity limits.
    :param location: Geographic location of the resource.
    :param partition_count: Number of partitions in the search service.
    :param replica_count: Number of replicas in the search service.
    """
    from azure.mgmt.search.models import SearchService, Sku
    from azure.cli.command_modules.search._client_factory import cf_search_services

    _client = cf_search_services(cmd.cli_ctx, None)
    if location is None:
        location = _get_resource_group_location(cmd.cli_ctx, resource_group_name)

    _search = SearchService(location=location, sku=Sku(name=sku))
    replica_count = int(replica_count)
    partition_count = int(partition_count)
    if replica_count > 0:
        _search.replica_count = replica_count
    if partition_count > 0:
        _search.partition_count = partition_count
    return _client.create_or_update(resource_group_name, search_service_name, _search)


def update_search_service(instance, partition_count=0, replica_count=0):
    """
    Update partition and replica of the given search service.

    :param partition_count: Number of partitions in the search service.
    :param replica_count: Number of replicas in the search service.
    """
    replica_count = int(replica_count)
    partition_count = int(partition_count)
    if replica_count > 0:
        instance.replica_count = replica_count
    if partition_count > 0:
        instance.partition_count = partition_count
    return instance
