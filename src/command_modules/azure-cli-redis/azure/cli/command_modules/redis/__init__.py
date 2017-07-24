# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands.parameters import get_resource_name_completion_list, name_type
from azure.cli.core.commands.arm import cli_generic_update_command

from azure.cli.command_modules.redis._client_factory import cf_redis, cf_patch_schedules
from azure.cli.command_modules.redis.custom import wrong_vmsize_argument_exception_handler
import azure.cli.command_modules.redis._help  # pylint: disable=unused-import
from azure.cli.command_modules.redis._validators import JsonString, ScheduleEntryList

from azure.mgmt.redis.models.redis_management_client_enums import RebootType, RedisKeyType, SkuName
from azure.mgmt.redis.models import ScheduleEntry

from knack.arguments import enum_choice_list


class RedisCommandsLoader(AzCommandsLoader):

    def load_command_table(self, args):
        super(RedisCommandsLoader, self).load_command_table(args)
        redis_operation = 'azure.mgmt.redis.operations.redis_operations#RedisOperations.'
        redis_custom = 'azure.cli.command_modules.redis.custom#'
        redis_patch_operation = 'azure.mgmt.redis.operations.patch_schedules_operations#PatchSchedulesOperations.'

        self.cli_command(__name__, 'redis create', redis_custom + 'cli_redis_create', client_factory=cf_redis, exception_handler=wrong_vmsize_argument_exception_handler)
        self.cli_command(__name__, 'redis delete', redis_operation + 'delete', client_factory=cf_redis)
        self.cli_command(__name__, 'redis export', redis_custom + 'cli_redis_export', client_factory=cf_redis)
        self.cli_command(__name__, 'redis force-reboot', redis_operation + 'force_reboot', client_factory=cf_redis)
        self.cli_command(__name__, 'redis import-method', redis_custom + 'cli_redis_import_method', client_factory=cf_redis)
        self.cli_command(__name__, 'redis list', redis_operation + 'list_by_resource_group', client_factory=cf_redis)
        self.cli_command(__name__, 'redis list-all', redis_operation + 'list', client_factory=cf_redis)
        self.cli_command(__name__, 'redis list-keys', redis_operation + 'list_keys', client_factory=cf_redis)
        self.cli_command(__name__, 'redis regenerate-keys', redis_operation + 'regenerate_key', client_factory=cf_redis)
        self.cli_command(__name__, 'redis show', redis_operation + 'get', client_factory=cf_redis)
        self.cli_command(__name__, 'redis update-settings', redis_custom + 'cli_redis_update_settings', client_factory=cf_redis)

        self.cli_generic_update_command(__name__, 'redis update',
                                        redis_operation + 'get',
                                        redis_operation + 'create_or_update',
                                        cf_redis,
                                        custom_function_op=redis_custom + 'cli_redis_update',
                                        exception_handler=wrong_vmsize_argument_exception_handler)

        self.cli_command(__name__, 'redis patch-schedule set', redis_patch_operation + 'create_or_update', client_factory=cf_patch_schedules)
        self.cli_command(__name__, 'redis patch-schedule delete', redis_patch_operation + 'delete', client_factory=cf_patch_schedules)
        self.cli_command(__name__, 'redis patch-schedule show', redis_patch_operation + 'get', client_factory=cf_patch_schedules)
        return self.command_table

    def load_arguments(self, command):
        self.register_cli_argument('redis', 'name', options_list=['--name', '-n'], help='Name of the redis cache.', completer=get_resource_name_completion_list('Microsoft.Cache/redis'))
        self.register_cli_argument('redis', 'redis_configuration', type=JsonString)
        self.register_cli_argument('redis', 'reboot_type', **enum_choice_list(RebootType))
        self.register_cli_argument('redis', 'key_type', **enum_choice_list(RedisKeyType))
        self.register_cli_argument('redis', 'shard_id', type=int)
        self.register_cli_argument('redis', 'sku', **enum_choice_list(SkuName))
        self.register_cli_argument('redis', 'vm_size', help='Size of redis cache to deploy. Example : values for C family (C0, C1, C2, C3, C4, C5, C6). For P family (P1, P2, P3, P4)')
        self.register_cli_argument('redis', 'enable_non_ssl_port', action='store_true')
        self.register_cli_argument('redis', 'shard_count', type=int)
        self.register_cli_argument('redis', 'subnet_id')

        self.register_cli_argument('redis import-method', 'files', nargs='+')

        self.register_cli_argument('redis patch-schedule set', 'schedule_entries', type=ScheduleEntryList)

        self.register_cli_argument('redis create', 'name', arg_type=name_type, completer=None)
        self.register_cli_argument('redis create', 'tenant_settings', type=JsonString)
        super(RedisCommandsLoader, self).load_arguments(command)
