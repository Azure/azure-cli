# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType


def load_command_table(self, _):
    from azure.cli.command_modules.eventhubs._client_factory import (namespaces_mgmt_client_factory,
                                                                     event_hub_mgmt_client_factory,
                                                                     consumer_groups_mgmt_client_factory,
                                                                     disaster_recovery_mgmt_client_factory,
                                                                     cluster_mgmt_client_factory)

    eh_namespace_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations#NamespacesOperations.{}',
        client_factory=namespaces_mgmt_client_factory,
        resource_type=ResourceType.MGMT_EVENTHUB)

    eh_clusters_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations#ClustersOperations.{}',
        client_factory=cluster_mgmt_client_factory,
        resource_type=ResourceType.MGMT_EVENTHUB)

    eh_event_hub_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations#EventHubsOperations.{}',
        client_factory=event_hub_mgmt_client_factory,
        resource_type=ResourceType.MGMT_EVENTHUB)

    eh_consumer_groups_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations#ConsumerGroupsOperations.{}',
        client_factory=consumer_groups_mgmt_client_factory,
        resource_type=ResourceType.MGMT_EVENTHUB)

    eh_geodr_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations#DisasterRecoveryConfigsOperations.{}',
        client_factory=disaster_recovery_mgmt_client_factory,
        resource_type=ResourceType.MGMT_EVENTHUB)

    from ._validator import validate_subnet


# Namespace Region
    custom_tmpl = 'azure.cli.command_modules.eventhubs.custom#{}'
    eventhubs_custom = CliCommandType(operations_tmpl=custom_tmpl)
    with self.command_group('eventhubs namespace', eh_namespace_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_namespace_create')
        g.show_command('show', 'get')
        g.custom_command('list', 'cli_namespace_list')
        g.command('delete', 'delete')
        g.command('exists', 'check_name_availability')
        g.generic_update_command('update', custom_func_name='cli_namespace_update', custom_func_type=eventhubs_custom)

    with self.command_group('eventhubs namespace authorization-rule', eh_namespace_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=namespaces_mgmt_client_factory) as g:
        g.command('create', 'create_or_update_authorization_rule')
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules')
        g.command('keys list', 'list_keys')
        g.command('keys renew', 'regenerate_keys')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_autho_update')

# Cluster Region
    with self.command_group('eventhubs cluster', eh_clusters_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=cluster_mgmt_client_factory, min_api='2018-01-01-preview') as g:
        g.custom_command('create', 'cli_cluster_create')
        g.show_command('show', 'get')
        g.command('list', 'list_by_resource_group')
        g.command('namespace list', 'list_namespaces')
        g.wait_command('wait')
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.command('available-region', 'list_available_cluster_region')
        g.generic_update_command('update', getter_name='get', setter_name='update', custom_func_name='cli_cluster_update', custom_func_type=eventhubs_custom)

# EventHub Region
    with self.command_group('eventhubs eventhub', eh_event_hub_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=event_hub_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_eheventhub_create')
        g.show_command('show', 'get')
        g.command('list', 'list_by_namespace')
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_eheventhub_update')

    with self.command_group('eventhubs eventhub authorization-rule', eh_event_hub_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=event_hub_mgmt_client_factory) as g:
        g.command('create', 'create_or_update_authorization_rule')
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules')
        g.command('keys list', 'list_keys')
        g.command('keys renew', 'regenerate_keys')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_autho_update')

# ConsumerGroup Region
    with self.command_group('eventhubs eventhub consumer-group', eh_consumer_groups_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=consumer_groups_mgmt_client_factory) as g:
        g.command('create', 'create_or_update')
        g.show_command('show', 'get')
        g.command('list', 'list_by_event_hub')
        g.command('delete', 'delete')
        g.generic_update_command('update')

# DisasterRecoveryConfigs Region
    with self.command_group('eventhubs georecovery-alias', eh_geodr_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=disaster_recovery_mgmt_client_factory) as g:
        g.command('set', 'create_or_update')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('break-pair', 'break_pairing')
        g.command('fail-over', 'fail_over')
        g.command('exists', 'check_name_availability')
        g.command('delete', 'delete')

    with self.command_group('eventhubs georecovery-alias authorization-rule', eh_geodr_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=disaster_recovery_mgmt_client_factory) as g:
        g.command('list', 'list_authorization_rules')
        g.show_command('show', 'get_authorization_rule')
        g.command('keys list', 'list_keys')

# NetwrokRuleSet Region
    with self.command_group('eventhubs namespace network-rule', eh_namespace_util, min_api='2017-04-01', resource_type=ResourceType.MGMT_EVENTHUB, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('add', 'cli_networkrule_createupdate', validator=validate_subnet)
        g.show_command('list', 'get_network_rule_set')
        g.custom_command('remove', 'cli_networkrule_delete', validator=validate_subnet)
