# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):
    from azure.cli.command_modules.servicebus._client_factory import namespaces_mgmt_client_factory, \
        queues_mgmt_client_factory, topics_mgmt_client_factory, subscriptions_mgmt_client_factory, \
        rules_mgmt_client_factory, disaster_recovery_mgmt_client_factory
    from azure.cli.command_modules.servicebus.custom import empty_on_404

    sb_namespace_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations.namespaces_operations#NamespacesOperations.{}',
        client_factory=namespaces_mgmt_client_factory
    )

    sb_queue_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations.queues_operations#QueuesOperations.{}',
        client_factory=queues_mgmt_client_factory
    )

    sb_topic_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations.topics_operations#TopicsOperations.{}',
        client_factory=topics_mgmt_client_factory
    )

    sb_subscriptions_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations.subscriptions_operations#SubscriptionsOperations.{}',
        client_factory=subscriptions_mgmt_client_factory
    )

    sb_rule_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations.rules_operations#RulesOperations.{}',
        client_factory=rules_mgmt_client_factory
    )

    sb_geodr_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicebus.operations.disaster_recovery_configs_operations#DisasterRecoveryConfigsOperations.{}',
        client_factory=disaster_recovery_mgmt_client_factory
    )

# Namespace Region
    custom_tmpl = 'azure.cli.command_modules.servicebus.custom#{}'
    servicebus_custom = CliCommandType(operations_tmpl=custom_tmpl)
    with self.command_group('servicebus namespace', sb_namespace_util, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_namespace_create')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.custom_command('list', 'cli_namespace_list', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.command('exists', 'check_name_availability_method')
        g.generic_update_command('update', custom_func_name='cli_namespace_update', custom_func_type=servicebus_custom)

    with self.command_group('servicebus namespace authorization-rule', sb_namespace_util, client_factory=namespaces_mgmt_client_factory) as g:
        g.command('create', 'create_or_update_authorization_rule',)
        g.command('show', 'get_authorization_rule', exception_handler=empty_on_404)
        g.command('list', 'list_authorization_rules', exception_handler=empty_on_404)
        g.command('keys list', 'list_keys')
        g.command('keys renew', 'regenerate_keys')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_namespaceautho_update')

# Queue Region
    with self.command_group('servicebus queue', sb_queue_util, client_factory=queues_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_sbqueue_create')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.command('list', 'list_by_namespace', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_sbqueue_update')

    with self.command_group('servicebus queue authorization-rule', sb_queue_util, client_factory=queues_mgmt_client_factory) as g:
        g.command('create', 'create_or_update_authorization_rule',)
        g.command('show', 'get_authorization_rule', exception_handler=empty_on_404)
        g.command('list', 'list_authorization_rules', exception_handler=empty_on_404)
        g.command('keys list', 'list_keys')
        g.command('keys renew', 'regenerate_keys')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_namespaceautho_update')

# Topic Region
    with self.command_group('servicebus topic', sb_topic_util, client_factory=topics_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_sbtopic_create')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.command('list', 'list_by_namespace', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_sbtopic_update')

    with self.command_group('servicebus topic authorization-rule', sb_topic_util, client_factory=topics_mgmt_client_factory) as g:
        g.command('create', 'create_or_update_authorization_rule')
        g.command('show', 'get_authorization_rule', exception_handler=empty_on_404)
        g.command('list', 'list_authorization_rules', exception_handler=empty_on_404)
        g.command('keys list', 'list_keys')
        g.command('keys renew', 'regenerate_keys')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_namespaceautho_update')

# Subscription Region
    with self.command_group('servicebus topic subscription', sb_subscriptions_util, client_factory=subscriptions_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_sbsubscription_create')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.command('list', 'list_by_topic', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_sbsubscription_update')

# Rules Region
    with self.command_group('servicebus topic subscription rule', sb_rule_util, client_factory=rules_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_rules_create')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.command('list', 'list_by_subscriptions', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_rules_update')

# DisasterRecoveryConfigs Region
    with self.command_group('servicebus georecovery-alias', sb_geodr_util, client_factory=disaster_recovery_mgmt_client_factory) as g:
        g.command('set', 'create_or_update')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.command('list', 'list', exception_handler=empty_on_404)
        g.command('break-pair', 'break_pairing')
        g.command('fail-over', 'fail_over')
        g.command('exists', 'check_name_availability_method')
        g.command('delete', 'delete')

# DisasterRecoveryConfigs Authorization Region
    with self.command_group('servicebus georecovery-alias authorization-rule', sb_geodr_util, client_factory=disaster_recovery_mgmt_client_factory) as g:
        g.command('list', 'list_authorization_rules')
        g.command('show', 'get_authorization_rule')
        g.command('keys list', 'list_keys')
