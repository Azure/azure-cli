# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.log import get_logger
from azure.mgmt.resource import ResourceManagementClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import sdk_no_wait

logger = get_logger(__name__)


def cluster_create(cmd,
                   client,
                   resource_group_name,
                   cluster_name,
                   sku,
                   location=None,
                   tier="Standard",
                   capacity=None,
                   tags=None,
                   custom_headers=None,
                   raw=False,
                   polling=True,
                   no_wait=False,
                   **kwargs):

    from azure.mgmt.kusto.models import Cluster, AzureSku
    from azure.cli.command_modules.kusto._client_factory import cf_cluster

    if location is None:
        location = _get_resource_group_location(cmd.cli_ctx, resource_group_name)

    _client = cf_cluster(cmd.cli_ctx, None)

    _cluster = Cluster(location=location, sku=AzureSku(name=sku, capacity=capacity))

    return sdk_no_wait(no_wait,
                       _client.create_or_update,
                       resource_group_name=resource_group_name,
                       cluster_name=cluster_name,
                       parameters=_cluster,
                       tags=tags,
                       custom_headers=custom_headers,
                       raw=raw,
                       polling=polling,
                       operation_config=kwargs)


def _cluster_get(cmd,
                 client,
                 resource_group_name,
                 cluster_name,
                 custom_headers=None,
                 raw=False,
                 polling=True,
                 no_wait=False,
                 **kwargs):

    from azure.mgmt.kusto.models import Cluster, AzureSku
    from azure.cli.command_modules.kusto._client_factory import cf_cluster

    _client = cf_cluster(cmd.cli_ctx, None)

    return _client.get(resource_group_name=resource_group_name,
                       cluster_name=cluster_name,
                       custom_headers=custom_headers,
                       raw=raw,
                       operation_config=kwargs)


def cluster_start(cmd,
                  client,
                  resource_group_name,
                  cluster_name,
                  custom_headers=None,
                  raw=False,
                  polling=True,
                  **kwargs):

    from azure.cli.command_modules.kusto._client_factory import cf_cluster

    _client = cf_cluster(cmd.cli_ctx, None)

    return _client.start(resource_group_name=resource_group_name,
                         cluster_name=cluster_name,
                         custom_headers=custom_headers,
                         raw=raw,
                         operation_config=kwargs)


def cluster_stop(cmd,
                 client,
                 resource_group_name,
                 cluster_name,
                 custom_headers=None,
                 raw=False,
                 polling=True,
                 **kwargs):

    from azure.cli.command_modules.kusto._client_factory import cf_cluster

    _client = cf_cluster(cmd.cli_ctx, None)

    return _client.stop(resource_group_name=resource_group_name,
                        cluster_name=cluster_name,
                        custom_headers=custom_headers,
                        raw=raw,
                        operation_config=kwargs)


def database_create(cmd,
                    client,
                    resource_group_name,
                    cluster_name,
                    database_name,
                    soft_delete_period_in_days,
                    hot_cache_period_in_days=None,
                    tags=None,
                    custom_headers=None,
                    raw=False,
                    polling=True,
                    no_wait=False,
                    **kwargs):

    from azure.mgmt.kusto.models import Database
    from azure.cli.command_modules.kusto._client_factory import cf_database

    _client = cf_database(cmd.cli_ctx, None)
    _cluster = _cluster_get(cmd, client, resource_group_name, cluster_name, custom_headers, raw, polling, no_wait, **kwargs)

    if no_wait:
        location = _cluster.output.location
    else:
        location = _cluster.location

    _database = Database(location=location, soft_delete_period_in_days=soft_delete_period_in_days, hot_cache_period_in_days=hot_cache_period_in_days)

    return sdk_no_wait(no_wait,
                       _client.create_or_update,
                       resource_group_name=resource_group_name,
                       cluster_name=cluster_name,
                       database_name=database_name,
                       parameters=_database,
                       custom_headers=custom_headers,
                       raw=raw,
                       polling=polling,
                       operation_config=kwargs)


def update_kusto_cluster(instance, sku_name=None, capacity=None):
    """
    Update sku kusto cluster.

    :param sku_name: the name of the sku.
    """
    from azure.mgmt.kusto.models import AzureSku
    if sku_name is None:
        sku_name = instance.sku.name
    if capacity is None:
        capacity = instance.sku.capacity
    instance.sku = AzureSku(name=sku_name, capacity=capacity)
    return instance


def update_kusto_database(instance, soft_delete_period_in_days, hot_cache_period_in_days=None):

    soft_delete_period_in_days = int(soft_delete_period_in_days)
    hot_cache_period_in_days = int(hot_cache_period_in_days)

    """
    Update sku kusto database.

    :param soft_delete_period_in_days: The number of days data should be kept before it stops being accessible to queries.
    :param hot_cache_period_in_days: The number of days of data that should be kept in cache for fast queries.
    """
    instance.soft_delete_period_in_days = soft_delete_period_in_days
    instance.hot_cache_period_in_days = hot_cache_period_in_days

    return instance


def _get_resource_group_location(cli_ctx, resource_group_name):

    client = get_mgmt_service_client(cli_ctx, ResourceManagementClient)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location
