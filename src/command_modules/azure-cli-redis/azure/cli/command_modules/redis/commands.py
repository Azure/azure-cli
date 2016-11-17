# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.redis._client_factory import (cf_redis, cf_patch_schedules)

cli_command(__name__, 'redis create', 'azure.cli.command_modules.redis.custom#cli_redis_create', cf_redis)
cli_command(__name__, 'redis delete', 'azure.mgmt.redis.operations.redis_operations#RedisOperations.delete', cf_redis)
cli_command(__name__, 'redis export', 'azure.cli.command_modules.redis.custom#cli_redis_export', cf_redis)
cli_command(__name__, 'redis force-reboot', 'azure.mgmt.redis.operations.redis_operations#RedisOperations.force_reboot', cf_redis)
cli_command(__name__, 'redis import-method', 'azure.cli.command_modules.redis.custom#cli_redis_import_method', cf_redis)
cli_command(__name__, 'redis list', 'azure.mgmt.redis.operations.redis_operations#RedisOperations.list_by_resource_group', cf_redis)
cli_command(__name__, 'redis list-all', 'azure.mgmt.redis.operations.redis_operations#RedisOperations.list', cf_redis)
cli_command(__name__, 'redis list-keys', 'azure.mgmt.redis.operations.redis_operations#RedisOperations.list_keys', cf_redis)
cli_command(__name__, 'redis regenerate-keys', 'azure.mgmt.redis.operations.redis_operations#RedisOperations.regenerate_key', cf_redis)
cli_command(__name__, 'redis show', 'azure.mgmt.redis.operations.redis_operations#RedisOperations.get', cf_redis)
cli_command(__name__, 'redis update-settings', 'azure.cli.command_modules.redis.custom#cli_redis_update_settings', cf_redis)

cli_command(__name__, 'redis patch-schedule set', 'azure.mgmt.redis.operations.patch_schedules_operations#PatchSchedulesOperations.create_or_update', cf_patch_schedules)
cli_command(__name__, 'redis patch-schedule delete', 'azure.mgmt.redis.operations.patch_schedules_operations#PatchSchedulesOperations.delete', cf_patch_schedules)
cli_command(__name__, 'redis patch-schedule show', 'azure.mgmt.redis.operations.patch_schedules_operations#PatchSchedulesOperations.get', cf_patch_schedules)

