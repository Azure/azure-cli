# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements


def load_command_table(self, _):
    from azure.cli.core.commands import CliCommandType
    from azure.cli.command_modules.eventhubs._client_factory import (namespaces_mgmt_client_factory,
                                                                     event_hub_mgmt_client_factory,
                                                                     consumer_groups_mgmt_client_factory,
                                                                     disaster_recovery_mgmt_client_factory)
    from .custom import empty_on_404

    eh_namespace_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations.namespaces_operations#NamespacesOperations.{}',
        client_factory=namespaces_mgmt_client_factory
    )

    eh_event_hub_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations.event_hubs_operations#EventHubsOperations.{}',
        client_factory=event_hub_mgmt_client_factory
    )

    eh_consumer_groups_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations.consumer_groups_operations#ConsumerGroupsOperations.{}',
        client_factory=consumer_groups_mgmt_client_factory
    )

    eh_geodr_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations.disaster_recovery_configs_operations#DisasterRecoveryConfigsOperations.{}',
        client_factory=disaster_recovery_mgmt_client_factory
    )

# Namespace Region
    custom_tmpl = 'azure.cli.command_modules.eventhubs.custom#{}'
    eventhubs_custom = CliCommandType(operations_tmpl=custom_tmpl)
    with self.command_group('eventhubs namespace', eh_namespace_util, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_namespace_create')
        g.show_command('show', 'get')
        g.custom_command('list', 'cli_namespace_list', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.command('exists', 'check_name_availability')
        g.generic_update_command('update', custom_func_name='cli_namespace_update', custom_func_type=eventhubs_custom)

    with self.command_group('eventhubs namespace authorization-rule', eh_namespace_util, client_factory=namespaces_mgmt_client_factory) as g:
        g.command('create', 'create_or_update_authorization_rule')
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules', exception_handler=empty_on_404)
        g.command('keys list', 'list_keys')
        g.command('keys renew', 'regenerate_keys')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_autho_update')

# EventHub Region
    with self.command_group('eventhubs eventhub', eh_event_hub_util, client_factory=event_hub_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_eheventhub_create')
        g.show_command('show', 'get')
        g.command('list', 'list_by_namespace', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_eheventhub_update')

    with self.command_group('eventhubs eventhub authorization-rule', eh_event_hub_util, client_factory=event_hub_mgmt_client_factory) as g:
        g.command('create', 'create_or_update_authorization_rule')
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules', exception_handler=empty_on_404)
        g.command('keys list', 'list_keys')
        g.command('keys renew', 'regenerate_keys')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_autho_update')

# ConsumerGroup Region
    with self.command_group('eventhubs eventhub consumer-group', eh_consumer_groups_util, client_factory=consumer_groups_mgmt_client_factory) as g:
        g.command('create', 'create_or_update')
        g.show_command('show', 'get')
        g.command('list', 'list_by_event_hub', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.generic_update_command('update')

# DisasterRecoveryConfigs Region
    with self.command_group('eventhubs georecovery-alias', eh_geodr_util, client_factory=disaster_recovery_mgmt_client_factory) as g:
        g.command('set', 'create_or_update')
        g.show_command('show', 'get')
        g.command('list', 'list', exception_handler=empty_on_404)
        g.command('break-pair', 'break_pairing')
        g.command('fail-over', 'fail_over')
        g.command('exists', 'check_name_availability')
        g.command('delete', 'delete')

    with self.command_group('eventhubs georecovery-alias authorization-rule', eh_geodr_util, client_factory=disaster_recovery_mgmt_client_factory) as g:
        g.command('list', 'list_authorization_rules')
        g.show_command('show', 'get_authorization_rule')
        g.command('keys list', 'list_keys')
