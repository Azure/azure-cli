# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.client_factory import get_mgmt_service_client


def get_kusto_management_client(cli_ctx, **_):
    from azure.mgmt.kusto import KustoManagementClient
    return get_mgmt_service_client(cli_ctx, KustoManagementClient)


def cf_cluster(cli_ctx, _):
    return get_kusto_management_client(cli_ctx).clusters


def cf_database(cli_ctx, _):
    return get_kusto_management_client(cli_ctx).databases


def cf_resource_groups(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                   subscription_id=subscription_id).resource_groups
