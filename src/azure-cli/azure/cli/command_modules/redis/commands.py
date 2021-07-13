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

    with self.command_group('redis', redis_sdk) as g:
        g.custom_command('create', 'cli_redis_create', client_factory=cf_redis)
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('export', 'cli_redis_export')
        g.custom_command('force-reboot', 'cli_redis_force_reboot', client_factory=cf_redis)
        g.custom_command('import-method', 'cli_redis_import', client_factory=cf_redis, deprecate_info=g.deprecate(redirect='redis import', hide=True))
        g.custom_command('import', 'cli_redis_import', client_factory=cf_redis)
        g.custom_command('list', 'cli_redis_list_cache')
        g.command('list-keys', 'list_keys')
        g.custom_command('regenerate-keys', 'cli_redis_regenerate_key', client_factory=cf_redis)
        g.show_command('show', 'get')
        g.generic_update_command('update', setter_name='update', custom_func_name='cli_redis_update')

    with self.command_group('redis patch-schedule', redis_patch) as g:
        g.custom_command('create', 'cli_redis_patch_schedule_create_or_update', client_factory=cf_patch_schedules)
        g.custom_command('update', 'cli_redis_patch_schedule_create_or_update', client_factory=cf_patch_schedules)
        g.custom_command('delete', 'cli_redis_patch_schedule_delete', client_factory=cf_patch_schedules)
        g.custom_show_command('show', 'cli_redis_patch_schedule_get', client_factory=cf_patch_schedules)

    with self.command_group('redis firewall-rules', redis_firewall_rules) as g:
        g.custom_command('create', 'cli_redis_firewall_create', client_factory=cf_firewall_rule)
        g.custom_command('update', 'cli_redis_firewall_create', client_factory=cf_firewall_rule)
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list_by_redis_resource')

    with self.command_group('redis server-link', redis_linked_server) as g:
        g.custom_command('create', 'cli_redis_create_server_link', client_factory=cf_linked_server)
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
