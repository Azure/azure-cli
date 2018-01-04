# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
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

    with self.command_group('eventgrid topic', topics_mgmt_util, client_factory=topics_factory) as g:
        g.command('create', 'create_or_update')
        g.command('show', 'get')
        g.command('key list', 'list_shared_access_keys')
        g.command('key regenerate', 'regenerate_key')
        g.command('delete', 'delete')
        g.custom_command('list', 'cli_topic_list')
        g.generic_update_command('update',
                                 getter_name='get',
                                 setter_name='update',
                                 client_factory=topics_factory)

    custom_tmpl = 'azure.cli.command_modules.eventgrid.custom#{}'
    eventgrid_custom = CliCommandType(operations_tmpl=custom_tmpl)

    with self.command_group('eventgrid event-subscription', client_factory=event_subscriptions_factory) as g:
        g.custom_command('create', 'cli_eventgrid_event_subscription_create')
        g.custom_command('show', 'cli_eventgrid_event_subscription_get')
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
        g.command('show', 'get')
        g.command('list-event-types', 'list_event_types')
