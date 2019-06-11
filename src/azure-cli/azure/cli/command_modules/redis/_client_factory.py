# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_redis(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.redis import RedisManagementClient
    return get_mgmt_service_client(cli_ctx, RedisManagementClient).redis


def cf_patch_schedules(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.redis import RedisManagementClient
    return get_mgmt_service_client(cli_ctx, RedisManagementClient).patch_schedules


def cf_firewall_rule(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.redis import RedisManagementClient
    return get_mgmt_service_client(cli_ctx, RedisManagementClient).firewall_rules


def cf_linked_server(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.redis import RedisManagementClient
    return get_mgmt_service_client(cli_ctx, RedisManagementClient).linked_server
