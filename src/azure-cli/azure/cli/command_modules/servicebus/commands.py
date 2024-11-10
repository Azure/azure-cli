# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals
# pylint: disable=reimported

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):
    sb_namespace_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.servicebus.operations.namespace_custom#{}',
    )
    sb_network_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.servicebus.operations.network_rule_set#{}',
    )

# Namespace Region
    with self.command_group('servicebus namespace', custom_command_type=sb_namespace_custom) as g:
        g.custom_command('create', 'create_servicebus_namespace', supports_no_wait=True)

    with self.command_group('servicebus namespace private-endpoint-connection', custom_command_type=sb_namespace_custom) as g:
        from ._validators import validate_private_endpoint_connection_id
        g.custom_command('approve', 'approve_private_endpoint_connection', validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection', validator=validate_private_endpoint_connection_id)
        g.custom_command('delete', 'delete_private_endpoint_connection', confirmation=True, validator=validate_private_endpoint_connection_id)

# Rules Region
    with self.command_group('servicebus topic subscription rule', custom_command_type=sb_namespace_custom) as g:
        g.custom_command('create', 'sb_rule_create', supports_no_wait=True)

# DisasterRecoveryConfigs Region
    with self.command_group('servicebus georecovery-alias', custom_command_type=sb_namespace_custom) as g:
        g.custom_command('set', 'set_georecovery_alias', supports_no_wait=True)

# NetwrokRuleSet Region
    with self.command_group('servicebus namespace network-rule-set ip-rule', custom_command_type=sb_network_custom) as g:
        g.custom_command('add', 'add_network_rule_set_ip_rule')
        g.custom_command('remove', 'remove_network_rule_set_ip_rule')

    with self.command_group('servicebus namespace network-rule-set virtual-network-rule', custom_command_type=sb_network_custom) as g:
        g.custom_command('add', 'add_virtual_network_rule')
        g.custom_command('remove', 'remove_virtual_network_rule')

# Identity Region
    with self.command_group('servicebus namespace identity', custom_command_type=sb_namespace_custom) as g:
        g.custom_command('assign', 'cli_add_identity')
        g.custom_command('remove', 'cli_remove_identity')

# Encryption Region
    with self.command_group('servicebus namespace encryption', custom_command_type=sb_namespace_custom) as g:
        g.custom_command('add', 'cli_add_encryption')
        g.custom_command('remove', 'cli_remove_encryption')

# Replica Location Region
    with self.command_group('servicebus namespace replica', custom_command_type=sb_namespace_custom) as g:
        g.custom_command('add', 'cli_add_location')
        g.custom_command('remove', 'cli_remove_location')
