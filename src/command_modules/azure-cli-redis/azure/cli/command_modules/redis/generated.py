#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from .custom import (
    cli_redis_create,
    cli_redis_import_method,
    cli_redis_export,
    cli_redis_update_settings
)
from azure.mgmt.redis import (
    RedisManagementClient
)
from azure.mgmt.redis.operations import (
    RedisOperations,
    PatchSchedulesOperations
)
from azure.cli.core.commands import cli_command
from azure.cli.core.commands.client_factory import get_mgmt_service_client

def _redis_client_factory(**_):
    return get_mgmt_service_client(RedisManagementClient)

factory = lambda args: _redis_client_factory(**args).redis

cli_command('redis create', cli_redis_create, factory)
cli_command('redis delete', RedisOperations.delete, factory)
cli_command('redis export', cli_redis_export, factory)
cli_command('redis force-reboot', RedisOperations.force_reboot, factory)
cli_command('redis import-method', cli_redis_import_method, factory)
cli_command('redis list', RedisOperations.list_by_resource_group, factory)
cli_command('redis list-all', RedisOperations.list, factory)
cli_command('redis list-keys', RedisOperations.list_keys, factory)
cli_command('redis regenerate-keys', RedisOperations.regenerate_key, factory)
cli_command('redis show', RedisOperations.get, factory)

cli_command('redis update-settings', cli_redis_update_settings, factory)

factory = lambda args: _redis_client_factory(**args).patch_schedules
cli_command('redis patch-schedule set', PatchSchedulesOperations.create_or_update, factory)
cli_command('redis patch-schedule delete', PatchSchedulesOperations.delete, factory)
cli_command('redis patch-schedule show', PatchSchedulesOperations.get, factory)

