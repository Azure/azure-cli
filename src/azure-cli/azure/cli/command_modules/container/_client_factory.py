# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _container_instance_client_factory(cli_ctx, *_):
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ContainerInstanceManagementClient)


def cf_container_groups(cli_ctx, *_):
    return _container_instance_client_factory(cli_ctx).container_groups


def cf_container(cli_ctx, *_):
    return _container_instance_client_factory(cli_ctx).container


def _log_analytics_client_factory(cli_ctx, *_):
    from azure.mgmt.loganalytics import LogAnalyticsManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, LogAnalyticsManagementClient)


def cf_log_analytics_workspace(cli_ctx, *_):
    return _log_analytics_client_factory(cli_ctx).workspaces


def cf_log_analytics_workspace_shared_keys(cli_ctx, *_):
    return _log_analytics_client_factory(cli_ctx).shared_keys


def cf_resource(cli_ctx):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


def get_auth_management_client(cli_ctx, scope=None, **_):
    import re
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    subscription_id = None
    if scope:
        matched = re.match('/subscriptions/(?P<subscription>[^/]*)/', scope)
        if matched:
            subscription_id = matched.groupdict()['subscription']
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION, subscription_id=subscription_id)


def cf_network(cli_ctx):
    from azure.mgmt.network import NetworkManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, NetworkManagementClient, api_version="2018-08-01")
