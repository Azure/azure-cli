# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

# pylint: disable=line-too-long
from azure.cli.command_modules.redis._client_factory import cf_redis, cf_patch_schedules, cf_firewall_rule, cf_linked_server


def load_command_table(self, _):
    redis_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.redis.operations#RedisOperations.{}',
        client_factory=cf_redis)

    redis_patch = CliCommandType(
        operations_tmpl='azure.mgmt.redis.operations#PatchSchedulesOperations.{}',
        client_factory=cf_patch_schedules)

    redis_firewall_rules = CliCommandType(
        operations_tmpl='azure.mgmt.redis.operations#FirewallRulesOperations.{}',
        client_factory=cf_firewall_rule)

    redis_linked_server = CliCommandType(
        operations_tmpl='azure.mgmt.redis.operations#LinkedServerOperations.{}',
        client_factory=cf_linked_server)

    redis_patch_schedules_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.redis.custom#{}',
        client_factory=cf_patch_schedules)
    redis_firewall_rules_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.redis.custom#{}',
        client_factory=cf_firewall_rule)
    redis_linked_server_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.redis.custom#{}',
        client_factory=cf_linked_server)

    with self.command_group('redis', redis_sdk) as g:
        g.custom_command('create', 'cli_redis_create')
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('export', 'cli_redis_export')
        g.custom_command('force-reboot', 'cli_redis_force_reboot')
        g.custom_command('import-method', 'cli_redis_import', deprecate_info=g.deprecate(redirect='redis import', hide=True))
        g.custom_command('import', 'cli_redis_import')
        g.custom_command('list', 'cli_redis_list_cache')
        g.command('list-keys', 'list_keys')
        g.custom_command('regenerate-keys', 'cli_redis_regenerate_key')
        g.show_command('show', 'get')
        g.generic_update_command('update', setter_name='update', custom_func_name='cli_redis_update')

    with self.command_group('redis patch-schedule', redis_patch, custom_command_type=redis_patch_schedules_custom) as g:
        g.custom_command('create', 'cli_redis_patch_schedule_create_or_update')
        g.custom_command('update', 'cli_redis_patch_schedule_create_or_update')
        g.custom_command('delete', 'cli_redis_patch_schedule_delete')
        g.custom_show_command('show', 'cli_redis_patch_schedule_get')

    with self.command_group('redis firewall-rules', redis_firewall_rules, custom_command_type=redis_firewall_rules_custom) as g:
        g.custom_command('create', 'cli_redis_firewall_create')
        g.custom_command('update', 'cli_redis_firewall_create')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list')

    with self.command_group('redis server-link', redis_linked_server, custom_command_type=redis_linked_server_custom) as g:
        g.custom_command('create', 'cli_redis_create_server_link')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list')

    with self.command_group('redis identity', redis_sdk) as g:
        g.custom_show_command('show', 'cli_redis_identity_show')
        g.custom_command('assign', 'cli_redis_identity_assign')
        g.custom_command('remove', 'cli_redis_identity_remove')
