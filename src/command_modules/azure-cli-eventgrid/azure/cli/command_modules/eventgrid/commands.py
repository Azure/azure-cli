# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.sdk.util import CliCommandType
from ._client_factory import (topics_factory, event_subscriptions_factory, topic_types_factory)


def load_command_table(self, _):
    topics_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations.topics_operations#TopicsOperations.{}',
        client_factory=topics_factory
    )

    topic_type_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.eventgrid.operations.topic_types_operations#TopicTypesOperations.{}',
        client_factory=topic_types_factory
    )

    with self.command_group('eventgrid topic', topics_mgmt_util) as g:
        g.command('create', 'create_or_update')
        g.command('show', 'get')
        g.command('key list', 'list_shared_access_keys')
        g.command('key regenerate', 'regenerate_key')
        g.command('delete', 'delete')
        g.custom_command('list', 'cli_topic_list')

    with self.command_group('eventgrid topic event-subscription', client_factory=event_subscriptions_factory) as g:
        g.custom_command('create', 'cli_eventgrid_event_subscription_topic_create')
        g.custom_command('show', 'cli_eventgrid_event_subscription_topic_get')
        g.custom_command('show-endpoint-url', 'cli_eventgrid_event_subscription_topic_get_full_url')
        g.custom_command('delete', 'cli_eventgrid_event_subscription_topic_delete')
        g.custom_command('list', 'cli_topic_event_subscription_list')

    with self.command_group('eventgrid event-subscription', client_factory=event_subscriptions_factory) as g:
        g.custom_command('create', 'cli_eventgrid_event_subscription_arm_create')
        g.custom_command('show', 'cli_eventgrid_event_subscription_arm_get')
        g.custom_command('show-endpoint-url', 'cli_eventgrid_event_subscription_arm_get_full_url')
        g.custom_command('delete', 'cli_eventgrid_event_subscription_arm_delete')
        g.custom_command('list', 'cli_event_subscription_list')

    with self.command_group('eventgrid resource event-subscription', client_factory=event_subscriptions_factory) as g:
        g.custom_command('create', 'cli_eventgrid_event_subscription_resource_create')
        g.custom_command('show', 'cli_eventgrid_event_subscription_resource_get')
        g.custom_command('show-endpoint-url', 'cli_eventgrid_event_subscription_resource_get_full_url')
        g.custom_command('delete', 'cli_eventgrid_event_subscription_resource_delete')
        g.custom_command('list', 'cli_resource_event_subscription_list')

    with self.command_group('eventgrid topic-type', topic_type_mgmt_util) as g:
        g.command('list', 'list')
        g.command('show', 'get')
        g.command('list-event-types', 'list_event_types')
