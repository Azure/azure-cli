# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals

from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType


def load_command_table(self, _):
    from azure.cli.command_modules.servicebus._client_factory import (namespaces_mgmt_client_factory,
                                                                      disaster_recovery_mgmt_client_factory,
                                                                      migration_mgmt_client_factory)

    sb_namespace_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations#NamespacesOperations.{}',
        client_factory=namespaces_mgmt_client_factory,
        resource_type=ResourceType.MGMT_SERVICEBUS)

    sb_namespace_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.servicebus.Operation.NamespaceCustomFile#{}',
    )

    sb_geodr_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations#DisasterRecoveryConfigsOperations.{}',
        client_factory=disaster_recovery_mgmt_client_factory,
        resource_type=ResourceType.MGMT_SERVICEBUS)

    sb_migration_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations#MigrationConfigsOperations.{}',
        client_factory=migration_mgmt_client_factory,
        resource_type=ResourceType.MGMT_SERVICEBUS)

    from ._validators import validate_subnet

# Namespace Region
    with self.command_group('servicebus namespace', custom_command_type=sb_namespace_custom,
                            is_preview=True) as g:
        g.custom_command('create', 'create_servicebus_namespace', supports_no_wait=True)

    with self.command_group('servicebus namespace', sb_namespace_util, client_factory=namespaces_mgmt_client_factory, min_api='2021-06-01-preview') as g:
        g.custom_command('exists', 'cli_namespace_exists')

    with self.command_group('servicebus namespace private-endpoint-connection', custom_command_type=sb_namespace_custom,
                            is_preview=True) as g:
        from ._validators import validate_private_endpoint_connection_id
        g.custom_command('approve', 'approve_private_endpoint_connection', validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection', validator=validate_private_endpoint_connection_id)
        g.custom_command('delete', 'delete_private_endpoint_connection', confirmation=True, validator=validate_private_endpoint_connection_id)

# Rules Region
    with self.command_group('servicebus topic subscription rule', custom_command_type=sb_namespace_custom,
                            is_preview=True) as g:
        g.custom_command('create', 'sb_rule_create', supports_no_wait=True)

# DisasterRecoveryConfigs Region
    with self.command_group('servicebus georecovery-alias', sb_geodr_util, client_factory=disaster_recovery_mgmt_client_factory, resource_type=ResourceType.MGMT_SERVICEBUS) as g:
        g.custom_command('set', 'cli_georecovery_alias_create')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('break-pair', 'break_pairing')
        g.command('fail-over', 'fail_over')
        g.custom_command('exists', 'cli_georecovery_alias_exists')
        g.command('delete', 'delete')

# DisasterRecoveryConfigs Authorization Region
    with self.command_group('servicebus georecovery-alias authorization-rule', sb_geodr_util, client_factory=disaster_recovery_mgmt_client_factory, resource_type=ResourceType.MGMT_SERVICEBUS) as g:
        g.command('list', 'list_authorization_rules')
        g.show_command('show', 'get_authorization_rule')
        g.command('keys list', 'list_keys')

# MigrationConfigs Region
    with self.command_group('servicebus migration', sb_migration_util, client_factory=migration_mgmt_client_factory, resource_type=ResourceType.MGMT_SERVICEBUS) as g:
        g.custom_command('start', 'cli_migration_start')
        g.custom_show_command('show', 'cli_migration_show')
        g.custom_command('complete', 'cli_migration_complete')
        g.custom_command('abort', 'revert')

# NetwrokRuleSet Region
    with self.command_group('servicebus namespace network-rule', sb_namespace_util, client_factory=namespaces_mgmt_client_factory, resource_type=ResourceType.MGMT_SERVICEBUS) as g:
        g.custom_command('add', 'cli_networkrule_createupdate', validator=validate_subnet)
        g.command('list', 'get_network_rule_set')
        g.custom_command('remove', 'cli_networkrule_delete', validator=validate_subnet)
        g.custom_command('update', 'cli_networkrule_update')

# Identity Region
    with self.command_group('servicebus namespace identity', custom_command_type=sb_namespace_custom, is_preview=True) as g:
        g.custom_command('assign', 'cli_add_identity')
        g.custom_command('remove', 'cli_remove_identity')

# Encryption Region
    with self.command_group('servicebus namespace encryption', custom_command_type=sb_namespace_custom, is_preview=True) as g:
        g.custom_command('add', 'cli_add_encryption')
        g.custom_command('remove', 'cli_remove_encryption')
