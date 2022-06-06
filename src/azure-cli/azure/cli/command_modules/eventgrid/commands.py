# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands import CliCommandType
from ._client_factory import (
    topics_factory,
    topic_event_subscriptions_factory,
    domains_factory,
    domain_topics_factory,
    system_topics_factory,
    system_topic_event_subscriptions_factory,
    event_subscriptions_factory,
    topic_types_factory,
    extension_topics_factory,
    partner_registrations_factory,
    partner_namespaces_factory,
    event_channels_factory,
    partner_topics_factory,
    partner_topic_event_subscriptions_factory
)


def load_command_table(self, _):
    topics_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#TopicsOperations.{}',
        client_factory=topics_factory,
        client_arg_name='self'
    )

    topic_event_subscriptions_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#TopicEventSubscriptionsOperations.{}',
        client_factory=topic_event_subscriptions_factory,
        client_arg_name='self'
    )

    extension_topics_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#ExtensionTopicsOperations.{}',
        client_factory=extension_topics_factory,
        client_arg_name='self'
    )

    domains_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#DomainsOperations.{}',
        client_factory=domains_factory,
        client_arg_name='self'
    )

    domain_topics_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#DomainTopicsOperations.{}',
        client_factory=domain_topics_factory,
        client_arg_name='self'
    )

    system_topics_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#SystemTopicsOperations.{}',
        client_factory=system_topics_factory,
        client_arg_name='self'
    )

    system_topic_event_subscriptions_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#SystemTopicEventSubscriptionsOperations.{}',
        client_factory=system_topic_event_subscriptions_factory,
        client_arg_name='self'
    )

    partner_registrations_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#PartnerRegistrationsOperations.{}',
        client_factory=partner_registrations_factory,
        client_arg_name='self'
    )

    partner_namespaces_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#PartnerNamespacesOperations.{}',
        client_factory=partner_namespaces_factory,
        client_arg_name='self'
    )

    event_channels_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#EventChannelsOperations.{}',
        client_factory=event_channels_factory,
        client_arg_name='self'
    )

    partner_topics_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#PartnerTopicsOperations.{}',
        client_factory=partner_topics_factory,
        client_arg_name='self'
    )

    partner_topic_event_subscriptions_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#PartnerTopicEventSubscriptionsOperations.{}',
        client_factory=partner_topic_event_subscriptions_factory,
        client_arg_name='self'
    )

    topic_type_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations#TopicTypesOperations.{}',
        client_factory=topic_types_factory,
        client_arg_name='self'
    )

    with self.command_group('eventgrid topic', topics_mgmt_util, client_factory=topics_factory) as g:
        g.show_command('show', 'get')
        g.command('key list', 'list_shared_access_keys')
        g.command('delete', 'begin_delete')
        g.custom_command('key regenerate', 'cli_topic_regenerate_key')
        g.custom_command('list', 'cli_topic_list')
        g.custom_command('create', 'cli_topic_create_or_update')
        g.custom_command('update', 'cli_topic_update')

    with self.command_group('eventgrid topic event-subscription', topic_event_subscriptions_mgmt_util, client_factory=topic_event_subscriptions_factory, is_preview=True) as g:
        g.custom_show_command('show', 'cli_topic_event_subscription_get')
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('list', 'cli_topic_event_subscription_list')
        g.custom_command('create', 'cli_topic_event_subscription_create_or_update')
        g.custom_command('update', 'cli_topic_event_subscription_update')

    with self.command_group('eventgrid extension-topic', extension_topics_mgmt_util, client_factory=extension_topics_factory) as g:
        g.show_command('show', 'get')

    with self.command_group('eventgrid domain topic', domain_topics_mgmt_util, client_factory=domain_topics_factory) as g:
        g.show_command('show', 'get')
        g.custom_command('list', 'cli_domain_topic_list')
        g.custom_command('delete', 'cli_domain_topic_delete')
        g.custom_command('create', 'cli_domain_topic_create_or_update')

    with self.command_group('eventgrid domain', domains_mgmt_util, client_factory=domains_factory) as g:
        g.show_command('show', 'get')
        g.command('key list', 'list_shared_access_keys')
        g.custom_command('key regenerate', 'cli_domain_regenerate_key')
        g.custom_command('list', 'cli_domain_list')
        g.custom_command('create', 'cli_domain_create_or_update')
        g.command('delete', 'begin_delete')
        g.custom_command('update', 'cli_domain_update')

    with self.command_group('eventgrid system-topic', system_topics_mgmt_util, client_factory=system_topics_factory) as g:
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('list', 'cli_system_topic_list')
        g.custom_command('create', 'cli_system_topic_create_or_update')
        g.custom_command('update', 'cli_system_topic_update')

    with self.command_group('eventgrid system-topic event-subscription', system_topic_event_subscriptions_mgmt_util, client_factory=system_topic_event_subscriptions_factory) as g:
        g.custom_show_command('show', 'cli_system_topic_event_subscription_get')
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('list', 'cli_system_topic_event_subscription_list')
        g.custom_command('create', 'cli_system_topic_event_subscription_create_or_update')
        g.custom_command('update', 'cli_system_topic_event_subscription_update')

    with self.command_group('eventgrid partner registration', partner_registrations_mgmt_util, client_factory=partner_registrations_factory, is_preview=True) as g:
        g.show_command('show', 'get')
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('list', 'cli_partner_registration_list')
        g.custom_command('create', 'cli_partner_registration_create_or_update')
        # g.custom_command('update', 'cli_partner_registration_update')

    with self.command_group('eventgrid partner namespace', partner_namespaces_mgmt_util, client_factory=partner_namespaces_factory, is_preview=True) as g:
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('list', 'cli_partner_namespace_list')
        g.custom_command('create', 'cli_partner_namespace_create_or_update')
        g.command('key list', 'list_shared_access_keys')
        g.custom_command('key regenerate', 'cli_partner_namespace_regenerate_key')
        # g.custom_command('update', 'cli_partner_namespace_update')

    with self.command_group('eventgrid partner namespace event-channel', event_channels_mgmt_util, client_factory=event_channels_factory, is_preview=True) as g:
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('list', 'cli_event_channel_list')
        # g.custom_command('update', 'cli_event_channel_update')
        g.custom_command('create', 'cli_event_channel_create_or_update')

    with self.command_group('eventgrid partner topic', partner_topics_mgmt_util, client_factory=partner_topics_factory, is_preview=True) as g:
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True)
        g.command('activate', 'activate')
        g.command('deactivate', 'deactivate')
        g.custom_command('list', 'cli_partner_topic_list')
        # g.custom_command('create', 'cli_partner_topic_create_or_update')
        # g.custom_command('update', 'cli_partner_topic_update')

    with self.command_group('eventgrid partner topic event-subscription', partner_topic_event_subscriptions_mgmt_util, client_factory=partner_topic_event_subscriptions_factory, is_preview=True) as g:
        g.custom_show_command('show', 'cli_partner_topic_event_subscription_get')
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('list', 'cli_partner_topic_event_subscription_list')
        g.custom_command('create', 'cli_partner_topic_event_subscription_create_or_update')
        g.custom_command('update', 'cli_partner_topic_event_subscription_update')

    custom_tmpl = 'azure.cli.command_modules.eventgrid.custom#{}'
    eventgrid_custom = CliCommandType(operations_tmpl=custom_tmpl)

    with self.command_group('eventgrid event-subscription', client_factory=event_subscriptions_factory) as g:
        g.custom_command('create', 'cli_eventgrid_event_subscription_create')
        g.custom_show_command('show', 'cli_eventgrid_event_subscription_get')
        g.custom_command('delete', 'cli_eventgrid_event_subscription_delete')
        g.custom_command('list', 'cli_event_subscription_list')
        g.generic_update_command('update',
                                 getter_type=eventgrid_custom,
                                 setter_type=eventgrid_custom,
                                 getter_name='event_subscription_getter',
                                 setter_name='event_subscription_setter',
                                 custom_func_name='update_event_subscription')

    with self.command_group('eventgrid topic-type', topic_type_mgmt_util) as g:
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.command('list-event-types', 'list_event_types')
