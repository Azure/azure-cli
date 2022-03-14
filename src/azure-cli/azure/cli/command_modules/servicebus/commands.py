# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType


def load_command_table(self, _):
    from azure.cli.command_modules.servicebus._client_factory import namespaces_mgmt_client_factory, \
        queues_mgmt_client_factory, topics_mgmt_client_factory, subscriptions_mgmt_client_factory, \
        rules_mgmt_client_factory, disaster_recovery_mgmt_client_factory, migration_mgmt_client_factory

    sb_namespace_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations#NamespacesOperations.{}',
        client_factory=namespaces_mgmt_client_factory
    )

    sb_queue_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations#QueuesOperations.{}',
        client_factory=queues_mgmt_client_factory
    )

    sb_topic_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations#TopicsOperations.{}',
        client_factory=topics_mgmt_client_factory
    )

    sb_subscriptions_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations#SubscriptionsOperations.{}',
        client_factory=subscriptions_mgmt_client_factory
    )

    sb_rule_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations#RulesOperations.{}',
        client_factory=rules_mgmt_client_factory
    )

    sb_geodr_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations#DisasterRecoveryConfigsOperations.{}',
        client_factory=disaster_recovery_mgmt_client_factory
    )

    sb_migration_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations#MigrationConfigsOperations.{}',
        client_factory=migration_mgmt_client_factory
    )

    from ._validators import validate_subnet

# Namespace Region
    custom_tmpl = 'azure.cli.command_modules.servicebus.custom#{}'
    servicebus_custom = CliCommandType(operations_tmpl=custom_tmpl)
    with self.command_group('servicebus namespace', sb_namespace_util, client_factory=namespaces_mgmt_client_factory, min_api='2021-06-01-preview') as g:
        g.custom_command('create', 'cli_namespace_create')
        g.show_command('show', 'get')
        g.custom_command('list', 'cli_namespace_list')
        g.command('delete', 'begin_delete')
        g.custom_command('exists', 'cli_namespace_exists')
        g.generic_update_command('update', custom_func_name='cli_namespace_update', custom_func_type=servicebus_custom, setter_name='begin_create_or_update')

    with self.command_group('servicebus namespace authorization-rule', sb_namespace_util, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_namespaceautho_create')
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules')
        g.command('keys list', 'list_keys')
        g.custom_command('keys renew', 'cli_keys_renew')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_namespaceautho_update')

# Queue Region
    with self.command_group('servicebus queue', sb_queue_util, client_factory=queues_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_sbqueue_create')
        g.show_command('show', 'get')
        g.command('list', 'list_by_namespace')
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_sbqueue_update')

    with self.command_group('servicebus queue authorization-rule', sb_queue_util, client_factory=queues_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_queueautho_create')
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules')
        g.command('keys list', 'list_keys')
        g.custom_command('keys renew', 'cli_queueauthokey_renew')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_namespaceautho_update')

# Topic Region
    with self.command_group('servicebus topic', sb_topic_util, client_factory=topics_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_sbtopic_create')
        g.show_command('show', 'get')
        g.command('list', 'list_by_namespace')
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_sbtopic_update')

    with self.command_group('servicebus topic authorization-rule', sb_topic_util, client_factory=topics_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_topicautho_create')
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules')
        g.command('keys list', 'list_keys')
        g.custom_command('keys renew', 'cli_topicauthokey_renew')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_namespaceautho_update')

# Subscription Region
    with self.command_group('servicebus topic subscription', sb_subscriptions_util, client_factory=subscriptions_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_sbsubscription_create')
        g.show_command('show', 'get')
        g.command('list', 'list_by_topic')
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_sbsubscription_update')

# Rules Region
    with self.command_group('servicebus topic subscription rule', sb_rule_util, client_factory=rules_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_rules_create')
        g.show_command('show', 'get')
        g.command('list', 'list_by_subscriptions')
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_rules_update')

# DisasterRecoveryConfigs Region
    with self.command_group('servicebus georecovery-alias', sb_geodr_util, client_factory=disaster_recovery_mgmt_client_factory) as g:
        g.custom_command('set', 'cli_georecovery_alias_create')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('break-pair', 'break_pairing')
        g.command('fail-over', 'fail_over')
        g.custom_command('exists', 'cli_georecovery_alias_exists')
        g.command('delete', 'delete')

# DisasterRecoveryConfigs Authorization Region
    with self.command_group('servicebus georecovery-alias authorization-rule', sb_geodr_util, client_factory=disaster_recovery_mgmt_client_factory) as g:
        g.command('list', 'list_authorization_rules')
        g.show_command('show', 'get_authorization_rule')
        g.command('keys list', 'list_keys')

# MigrationConfigs Region
    with self.command_group('servicebus migration', sb_migration_util, client_factory=migration_mgmt_client_factory) as g:
        g.custom_command('start', 'cli_migration_start')
        g.custom_show_command('show', 'cli_migration_show')
        g.custom_command('complete', 'cli_migration_complete')
        g.command('abort', 'revert')

# NetwrokRuleSet Region
    with self.command_group('servicebus namespace network-rule', sb_namespace_util, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('add', 'cli_networkrule_createupdate', validator=validate_subnet)
        g.command('list', 'get_network_rule_set')
        g.custom_command('remove', 'cli_networkrule_delete', validator=validate_subnet)

# Identity Region
    with self.command_group('servicebus namespace identity', sb_namespace_util, min_api='2021-06-01-preview', resource_type=ResourceType.MGMT_SERVICEBUS, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('assign', 'cli_add_identity')
        g.custom_command('remove', 'cli_remove_identity')

# Encryption Region
    with self.command_group('servicebus namespace encryption', sb_namespace_util, min_api='2021-06-01-preview', resource_type=ResourceType.MGMT_SERVICEBUS, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('add', 'cli_add_encryption')
        g.custom_command('remove', 'cli_remove_encryption')
