# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.command_modules.redis._client_factory import (cf_redis, cf_patch_schedules)
from azure.cli.command_modules.redis.custom import wrong_vmsize_argument_exception_handler

redis_operation = 'azure.mgmt.redis.operations.redis_operations#RedisOperations.'
redis_custom = 'azure.cli.command_modules.redis.custom#'
redis_patch_operation = \
    'azure.mgmt.redis.operations.patch_schedules_operations#PatchSchedulesOperations.'

cli_command(__name__, 'redis create', redis_custom + 'cli_redis_create', cf_redis,
            exception_handler=wrong_vmsize_argument_exception_handler)
cli_command(__name__, 'redis delete', redis_operation + 'delete', cf_redis)
cli_command(__name__, 'redis export', redis_custom + 'cli_redis_export', cf_redis)
cli_command(__name__, 'redis force-reboot', redis_operation + 'force_reboot', cf_redis)
cli_command(__name__, 'redis import-method', redis_custom + 'cli_redis_import_method', cf_redis)
cli_command(__name__, 'redis list', redis_operation + 'list_by_resource_group', cf_redis)
cli_command(__name__, 'redis list-all', redis_operation + 'list', cf_redis)
cli_command(__name__, 'redis list-keys', redis_operation + 'list_keys', cf_redis)
cli_command(__name__, 'redis regenerate-keys', redis_operation + 'regenerate_key', cf_redis)
cli_command(__name__, 'redis show', redis_operation + 'get', cf_redis)
cli_command(__name__, 'redis update-settings', redis_custom + 'cli_redis_update_settings', cf_redis)

cli_generic_update_command(__name__, 'redis update',
                           redis_operation + 'get',
                           redis_operation + 'create_or_update',
                           cf_redis,
                           custom_function_op=redis_custom + 'cli_redis_update',
                           exception_handler=wrong_vmsize_argument_exception_handler)

cli_command(__name__, 'redis patch-schedule set', redis_patch_operation + 'create_or_update',
            cf_patch_schedules)
cli_command(__name__, 'redis patch-schedule delete', redis_patch_operation + 'delete',
            cf_patch_schedules)
cli_command(__name__, 'redis patch-schedule show', redis_patch_operation + 'get',
            cf_patch_schedules)
