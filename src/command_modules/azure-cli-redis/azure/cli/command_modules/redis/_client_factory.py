# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_redis(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.redis import RedisManagementClient
    return get_mgmt_service_client(RedisManagementClient).redis


def cf_patch_schedules(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.redis import RedisManagementClient
    return get_mgmt_service_client(RedisManagementClient).patch_schedules
