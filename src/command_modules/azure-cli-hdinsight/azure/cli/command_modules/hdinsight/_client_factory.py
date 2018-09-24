# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_resource_groups(cli_ctx, subscription_id=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                   subscription_id=subscription_id).resource_groups


def cf_storage(cli_ctx, *_, **__):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.storage import StorageManagementClient
    return get_mgmt_service_client(cli_ctx, StorageManagementClient)


def cf_hdinsight(cli_ctx, *_, **__):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.hdinsight import HDInsightManagementClient
    return get_mgmt_service_client(cli_ctx, HDInsightManagementClient)


def cf_hdinsight_clusters(cli_ctx, *_, **__):
    return cf_hdinsight(cli_ctx).clusters
