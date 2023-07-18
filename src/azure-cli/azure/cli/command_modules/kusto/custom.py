# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from enum import Enum
from knack.log import get_logger
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import sdk_no_wait

logger = get_logger(__name__)


class AzureSkuName(Enum):
    # TODO: use AzureSkuName from Kusto python module in the new kusto python version
    standard_ds13_v21_tb_ps = "Standard_DS13_v2+1TB_PS"
    standard_ds13_v22_tb_ps = "Standard_DS13_v2+2TB_PS"
    standard_ds14_v23_tb_ps = "Standard_DS14_v2+3TB_PS"
    standard_ds14_v24_tb_ps = "Standard_DS14_v2+4TB_PS"
    standard_d13_v2 = "Standard_D13_v2"
    standard_d14_v2 = "Standard_D14_v2"
    standard_l8s = "Standard_L8s"
    standard_l16s = "Standard_L16s"
    standard_d11_v2 = "Standard_D11_v2"
    standard_d12_v2 = "Standard_D12_v2"
    standard_l4s = "Standard_L4s"
    dev_no_sla_standard_d11_v2 = "Dev(No SLA)_Standard_D11_v2"
    standard_e2a_v4 = "Standard_E2a_v4"
    standard_e4a_v4 = "Standard_E4a_v4"
    standard_e8a_v4 = "Standard_E8a_v4"
    standard_e16a_v4 = "Standard_E16a_v4"
    standard_e8as_v41_tb_ps = "Standard_E8as_v4+1TB_PS"
    standard_e8as_v42_tb_ps = "Standard_E8as_v4+2TB_PS"
    standard_e16as_v43_tb_ps = "Standard_E16as_v4+3TB_PS"
    standard_e16as_v44_tb_ps = "Standard_E16as_v4+4TB_PS"
    dev_no_sla_standard_e2a_v4 = "Dev(No SLA)_Standard_E2a_v4"


def cluster_create(cmd,
                   resource_group_name,
                   cluster_name,
                   sku,
                   location=None,
                   capacity=None,
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
                       custom_headers=custom_headers,
                       raw=raw,
                       polling=polling,
                       operation_config=kwargs)


def _cluster_get(cmd,
                 resource_group_name,
                 cluster_name,
                 custom_headers=None,
                 raw=False,
                 **kwargs):

    from azure.cli.command_modules.kusto._client_factory import cf_cluster

    _client = cf_cluster(cmd.cli_ctx, None)

    return _client.get(resource_group_name=resource_group_name,
                       cluster_name=cluster_name,
                       custom_headers=custom_headers,
                       raw=raw,
                       operation_config=kwargs)


def cluster_start(cmd,
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
                         polling=polling,
                         operation_config=kwargs)


def cluster_stop(cmd,
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
                        polling=polling,
                        operation_config=kwargs)


def database_create(cmd,
                    resource_group_name,
                    cluster_name,
                    database_name,
                    soft_delete_period=None,
                    hot_cache_period=None,
                    custom_headers=None,
                    raw=False,
                    polling=True,
                    no_wait=False,
                    **kwargs):

    from azure.mgmt.kusto.models import Database
    from azure.cli.command_modules.kusto._client_factory import cf_database

    _client = cf_database(cmd.cli_ctx, None)
    _cluster = _cluster_get(cmd, resource_group_name, cluster_name, custom_headers, raw, **kwargs)

    if no_wait:
        location = _cluster.output.location
    else:
        location = _cluster.location

    _database = Database(location=location,
                         soft_delete_period=soft_delete_period,
                         hot_cache_period=hot_cache_period)

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


def update_kusto_cluster(instance, sku=None, capacity=None):

    from azure.mgmt.kusto.models import AzureSku
    if sku is None:
        sku = instance.sku.name
    if capacity is None:
        capacity = instance.sku.capacity
    instance.sku = AzureSku(name=sku, capacity=capacity)
    return instance


def update_kusto_database(instance, soft_delete_period, hot_cache_period=None):

    instance.soft_delete_period = soft_delete_period
    instance.hot_cache_period = hot_cache_period

    return instance


def _get_resource_group_location(cli_ctx, resource_group_name):
    from azure.cli.core.profiles import ResourceType
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location
