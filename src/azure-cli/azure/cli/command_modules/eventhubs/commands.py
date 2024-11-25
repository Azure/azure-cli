# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):
    eh_namespace_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.eventhubs.operations.namespace_custom#{}',
    )

    eh_appgroup_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.eventhubs.operations.app_group_custom_file#{}'
    )

    eh_eventhub_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.eventhubs.operations.event_hub_entity#{}',
    )

    eh_network_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.eventhubs.operations.network_rule_set#{}'
    )

# Namespace Region
    with self.command_group('eventhubs namespace', custom_command_type=eh_namespace_custom) as g:
        g.custom_command('create', 'create_eventhub_namespace')

    with self.command_group('eventhubs namespace private-endpoint-connection', custom_command_type=eh_namespace_custom) as g:
        from ._validator import validate_private_endpoint_connection_id
        g.custom_command('approve', 'approve_private_endpoint_connection', validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection', validator=validate_private_endpoint_connection_id)
        g.custom_command('delete', 'delete_private_endpoint_connection', confirmation=True, validator=validate_private_endpoint_connection_id)

# EventHub Region
    from .operations.event_hub_entity import EventHubEntityUpdate
    self.command_table['eventhubs eventhub update'] = EventHubEntityUpdate(loader=self)
    with self.command_group('eventhubs eventhub', custom_command_type=eh_eventhub_custom) as g:
        g.custom_command('create', 'cli_eventhub_create')

# DisasterRecoveryConfigs Region
    with self.command_group('eventhubs georecovery-alias', custom_command_type=eh_namespace_custom) as g:
        g.custom_command('set', 'set_georecovery_alias', supports_no_wait=True)

# NetworkRuleSet Region
    with self.command_group('eventhubs namespace network-rule-set ip-rule', custom_command_type=eh_network_custom) as g:
        g.custom_command('add', 'add_network_rule_set_ip_rule')
        g.custom_command('remove', 'remove_network_rule_set_ip_rule')

    with self.command_group('eventhubs namespace network-rule-set virtual-network-rule', custom_command_type=eh_network_custom) as g:
        g.custom_command('add', 'add_virtual_network_rule')
        g.custom_command('remove', 'remove_virtual_network_rule')

# Identity Region
    with self.command_group('eventhubs namespace identity', custom_command_type=eh_namespace_custom) as g:
        g.custom_command('assign', 'cli_add_identity')
        g.custom_command('remove', 'cli_remove_identity')

# Encryption Region
    with self.command_group('eventhubs namespace encryption', custom_command_type=eh_namespace_custom) as g:
        g.custom_command('add', 'cli_add_encryption')
        g.custom_command('remove', 'cli_remove_encryption')

# ApplicationGroup Region
    with self.command_group('eventhubs namespace application-group', custom_command_type=eh_appgroup_custom) as g:
        g.custom_command('create', 'cli_appgroup_create')

    with self.command_group('eventhubs namespace application-group policy', custom_command_type=eh_appgroup_custom) as g:
        g.custom_command('add', 'cli_add_appgroup_policy')
        g.custom_command('remove', 'cli_remove_appgroup_policy')
# Replica Location Region
    with self.command_group('eventhubs namespace replica', custom_command_type=eh_namespace_custom) as g:
        g.custom_command('add', 'cli_add_location')
        g.custom_command('remove', 'cli_remove_location')
