# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):
    from azure.cli.command_modules.redis._client_factory import cf_redis, cf_patch_schedules
    from azure.cli.command_modules.redis.custom import wrong_vmsize_argument_exception_handler

    redis_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.redis.operations.redis_operations#RedisOperations.{}',
        client_factory=cf_redis)

    redis_patch = CliCommandType(
        operations_tmpl='azure.mgmt.redis.operations.patch_schedules_operations#PatchSchedulesOperations.{}',
        client_factory=cf_patch_schedules)

    with self.command_group('redis', redis_sdk) as g:
        g.custom_command('create', 'cli_redis_create', client_factory=cf_redis,
                         exception_handler=wrong_vmsize_argument_exception_handler)
        g.command('delete', 'delete')
        g.custom_command('export', 'cli_redis_export')
        g.command('force-reboot', 'force_reboot')
        g.custom_command('import-method', 'cli_redis_import_method',
                         deprecate_info=g.deprecate(redirect='redis import', hide='2.0.34'))
        g.custom_command('import', 'cli_redis_import_method')
        g.custom_command('list', 'cli_redis_list')
        g.command('list-all', 'list', deprecate_info=g.deprecate(redirect='redis list', hide='2.0.34'))
        g.command('list-keys', 'list_keys')
        g.command('regenerate-keys', 'regenerate_key')
        g.show_command('show', 'get')
        g.custom_command('update-settings', 'cli_redis_update_settings',
                         deprecate_info=g.deprecate(redirect='redis update', hide='2.0.34'))
        g.generic_update_command('update', exception_handler=wrong_vmsize_argument_exception_handler,
                                 setter_name='update', custom_func_name='cli_redis_update')

    with self.command_group('redis patch-schedule', redis_patch) as g:
        g.command('set', 'create_or_update')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
