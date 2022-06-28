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
                                                                     cluster_mgmt_client_factory,
                                                                     private_endpoint_connections_mgmt_client_factory,
                                                                     private_link_mgmt_client_factory,
                                                                     schema_registry_mgmt_client_factory,
                                                                     application_group_mgmt_client_factory)

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

    eh_private_endpoints_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations#PrivateEndpointConnectionsOperations.{}',
        client_factory=private_endpoint_connections_mgmt_client_factory,
        resource_type=ResourceType.MGMT_EVENTHUB)

    eh_private_links_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations#PrivateLinkResourcesOperations.{}',
        client_factory=private_link_mgmt_client_factory,
        resource_type=ResourceType.MGMT_EVENTHUB)

    eh_schema_registry_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations#SchemaRegistryOperations.{}',
        client_factory=schema_registry_mgmt_client_factory,
        resource_type=ResourceType.MGMT_EVENTHUB
    )

    eh_application_group_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventhub.operations#ApplicationGroupOperations.{}',
        client_factory=schema_registry_mgmt_client_factory,
        resource_type=ResourceType.MGMT_EVENTHUB
    )

    from ._validator import validate_subnet


# Namespace Region
    custom_tmpl = 'azure.cli.command_modules.eventhubs.custom#{}'
    eventhubs_custom = CliCommandType(operations_tmpl=custom_tmpl)
    with self.command_group('eventhubs namespace', eh_namespace_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_namespace_create')
        g.show_command('show', 'get')
        g.custom_command('list', 'cli_namespace_list')
        g.command('delete', 'begin_delete')
        g.custom_command('exists', 'cli_namespace_exists')
        g.generic_update_command('update', custom_func_name='cli_namespace_update', custom_func_type=eventhubs_custom, setter_name='begin_create_or_update')

    with self.command_group('eventhubs namespace authorization-rule', eh_namespace_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_namespaceautho_create')
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules')
        g.command('keys list', 'list_keys')
        g.custom_command('keys renew', 'cli_keys_renew')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_autho_update')

    with self.command_group('eventhubs namespace private-endpoint-connection', eh_private_endpoints_util, resource_type=ResourceType.MGMT_EVENTHUB,
                            custom_command_type=eventhubs_custom, is_preview=True,
                            client_factory=private_endpoint_connections_mgmt_client_factory) as g:
        from ._validator import validate_private_endpoint_connection_id
        g.command('delete', 'begin_delete', confirmation=True, validator=validate_private_endpoint_connection_id)
        g.show_command('show', 'get', validator=validate_private_endpoint_connection_id)
        g.command('list', 'list', validator=validate_private_endpoint_connection_id)
        g.custom_command('approve', 'approve_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id)

    with self.command_group('eventhubs namespace private-link-resource', eh_private_links_util,
                            resource_type=ResourceType.MGMT_EVENTHUB) as g:
        from azure.cli.core.commands.transform import gen_dict_to_list_transform
        g.show_command('show', 'get', is_preview=True, min_api='2021-06-01-preview',
                       transform=gen_dict_to_list_transform(key="value"))

# Cluster Region
    with self.command_group('eventhubs cluster', eh_clusters_util, resource_type=ResourceType.MGMT_EVENTHUB,
                            client_factory=cluster_mgmt_client_factory, min_api='2018-01-01-preview') as g:
        g.custom_command('create', 'cli_cluster_create')
        g.show_command('show', 'get')
        g.command('list', 'list_by_resource_group')
        g.command('namespace list', 'list_namespaces')
        g.wait_command('wait')
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.command('available-region', 'list_available_cluster_region')
        g.generic_update_command('update', getter_name='get', setter_name='begin_update',
                                 custom_func_name='cli_cluster_update', custom_func_type=eventhubs_custom)

# EventHub Region
    with self.command_group('eventhubs eventhub', eh_event_hub_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=event_hub_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_eheventhub_create')
        g.show_command('show', 'get')
        g.command('list', 'list_by_namespace')
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_eheventhub_update')

    with self.command_group('eventhubs eventhub authorization-rule', eh_event_hub_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=event_hub_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_eventhubautho_create')
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules')
        g.command('keys list', 'list_keys')
        g.custom_command('keys renew', 'cli_eventhub_keys_renew')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_autho_update')

# ConsumerGroup Region
    with self.command_group('eventhubs eventhub consumer-group', eh_consumer_groups_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=consumer_groups_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_consumergroup_create')
        g.show_command('show', 'get')
        g.command('list', 'list_by_event_hub')
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_consumergroup_update', custom_func_type=eventhubs_custom)

# DisasterRecoveryConfigs Region
    with self.command_group('eventhubs georecovery-alias', eh_geodr_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=disaster_recovery_mgmt_client_factory) as g:
        g.custom_command('set', 'cli_geodr_create')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('break-pair', 'break_pairing')
        g.command('fail-over', 'fail_over')
        g.custom_command('exists', 'cli_geodr_name_exists')
        g.command('delete', 'delete')

    with self.command_group('eventhubs georecovery-alias authorization-rule', eh_geodr_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=disaster_recovery_mgmt_client_factory) as g:
        g.command('list', 'list_authorization_rules')
        g.show_command('show', 'get_authorization_rule')
        g.command('keys list', 'list_keys')

# NetwrokRuleSet Region
    with self.command_group('eventhubs namespace network-rule', eh_namespace_util, min_api='2021-06-01-preview', resource_type=ResourceType.MGMT_EVENTHUB, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('add', 'cli_networkrule_createupdate', validator=validate_subnet)
        g.show_command('list', 'get_network_rule_set')
        g.custom_command('remove', 'cli_networkrule_delete', validator=validate_subnet)
        g.custom_command('update', 'cli_networkrule_update')

# Identity Region
    with self.command_group('eventhubs namespace identity', eh_namespace_util, min_api='2021-06-01-preview', resource_type=ResourceType.MGMT_EVENTHUB, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('assign', 'cli_add_identity')
        g.custom_command('remove', 'cli_remove_identity')

# Encryption Region
    with self.command_group('eventhubs namespace encryption', eh_namespace_util, min_api='2021-06-01-preview', resource_type=ResourceType.MGMT_EVENTHUB, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('add', 'cli_add_encryption')
        g.custom_command('remove', 'cli_remove_encryption')

# SchemaRegistry Region
    with self.command_group('eventhubs namespace schema-registry', eh_schema_registry_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=schema_registry_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_schemaregistry_createupdate')
        g.command('list', 'list_by_namespace')
        g.show_command('show', 'get')
        g.command('delete', 'delete')

# ApplicationGroup Region
    with self.command_group('eventhubs namespace application-group', eh_application_group_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=application_group_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_appgroup_create')
        g.custom_command('update', 'cli_appgroup_update')
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.command('list', 'list_by_namespace')

    with self.command_group('eventhubs namespace application-group application-group-policy', eh_application_group_util, resource_type=ResourceType.MGMT_EVENTHUB, client_factory=application_group_mgmt_client_factory) as g:
        g.custom_command('add', 'cli_add_appgroup_policy')
        g.custom_command('remove', 'cli_remove_appgroup_policy')
