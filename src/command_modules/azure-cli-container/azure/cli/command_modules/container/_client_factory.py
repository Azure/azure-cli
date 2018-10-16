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


def cf_log_analytics(cli_ctx, *_):
    return _log_analytics_client_factory(cli_ctx).workspaces


def cf_resource(cli_ctx):
    from azure.mgmt.resource import ResourceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceManagementClient)


def cf_network(cli_ctx):
    from azure.mgmt.network import NetworkManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, NetworkManagementClient, api_version="2018-08-01")
