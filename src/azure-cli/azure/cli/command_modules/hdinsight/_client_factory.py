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


def cf_network(cli_ctx, aux_subscriptions=None, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK,
                                   aux_subscriptions=aux_subscriptions)


def cf_graph(cli_ctx, **_):
    from azure.cli.command_modules.role import graph_client_factory
    client = graph_client_factory(cli_ctx)
    return client


def cf_resources(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


def cf_log_analytics(cli_ctx, *_, **__):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.loganalytics import LogAnalyticsManagementClient
    return get_mgmt_service_client(cli_ctx, LogAnalyticsManagementClient)


def cf_hdinsight(cli_ctx, *_, **__):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.hdinsight import HDInsightManagementClient
    return get_mgmt_service_client(cli_ctx, HDInsightManagementClient)


def cf_hdinsight_clusters(cli_ctx, *_, **__):
    return cf_hdinsight(cli_ctx).clusters


def cf_hdinsight_script_actions(cli_ctx, *_, **__):
    return cf_hdinsight(cli_ctx).script_actions


def cf_hdinsight_script_execution_history(cli_ctx, *_, **__):
    return cf_hdinsight(cli_ctx).script_execution_history


def cf_hdinsight_applications(cli_ctx, *_, **__):
    return cf_hdinsight(cli_ctx).applications


def cf_hdinsight_extensions(cli_ctx, *_, **__):
    return cf_hdinsight(cli_ctx).extensions


def cf_hdinsight_locations(cli_ctx, *_, **__):
    return cf_hdinsight(cli_ctx).locations


def cf_hdinsight_virtual_machines(cli_ctx, *_, **__):
    return cf_hdinsight(cli_ctx).virtual_machines
