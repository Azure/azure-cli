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


def cf_container_logs(cli_ctx, *_):
    return _container_instance_client_factory(cli_ctx).container_logs


def cf_start_container(cli_ctx, *_):
    return _container_instance_client_factory(cli_ctx).start_container
