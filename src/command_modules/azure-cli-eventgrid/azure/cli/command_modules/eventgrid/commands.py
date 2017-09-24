# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
from ._client_factory import (topics_factory, event_subscriptions_factory, topic_types_factory)

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
    topics_mgmt_path = 'azure.mgmt.eventgrid.operations.topics_operations#'
    topic_types_mgmt_path = 'azure.mgmt.eventgrid.operations.topic_types_operations#'
    custom_path = 'azure.cli.command_modules.eventgrid.custom#'

    cli_command(__name__, 'eventgrid topic create', topics_mgmt_path + 'TopicsOperations.create_or_update', topics_factory)
    cli_command(__name__, 'eventgrid topic show', topics_mgmt_path + 'TopicsOperations.get', topics_factory)
    cli_command(__name__, 'eventgrid topic key list', topics_mgmt_path + 'TopicsOperations.list_shared_access_keys', topics_factory)
    cli_command(__name__, 'eventgrid topic key regenerate', topics_mgmt_path + 'TopicsOperations.regenerate_key', topics_factory)
    cli_command(__name__, 'eventgrid topic delete', topics_mgmt_path + 'TopicsOperations.delete', topics_factory)
    cli_command(__name__, 'eventgrid topic list', custom_path + 'cli_topic_list', topics_factory)

    cli_command(__name__, 'eventgrid event-subscription create', custom_path + 'cli_eventgrid_event_subscription_arm_create', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid event-subscription show', custom_path + 'cli_eventgrid_event_subscription_arm_get', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid event-subscription show-endpoint-url', custom_path + 'cli_eventgrid_event_subscription_arm_get_full_url', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid event-subscription delete', custom_path + 'cli_eventgrid_event_subscription_arm_delete', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid event-subscription list', custom_path + 'cli_event_subscription_list', event_subscriptions_factory)

    cli_command(__name__, 'eventgrid topic event-subscription create', custom_path + 'cli_eventgrid_event_subscription_topic_create', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid topic event-subscription show', custom_path + 'cli_eventgrid_event_subscription_topic_get', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid topic event-subscription show-endpoint-url', custom_path + 'cli_eventgrid_event_subscription_topic_get_full_url', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid topic event-subscription delete', custom_path + 'cli_eventgrid_event_subscription_topic_delete', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid topic event-subscription list', custom_path + 'cli_topic_event_subscription_list', event_subscriptions_factory)

    cli_command(__name__, 'eventgrid resource event-subscription create', custom_path + 'cli_eventgrid_event_subscription_resource_create', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid resource event-subscription show', custom_path + 'cli_eventgrid_event_subscription_resource_get', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid resource event-subscription show-endpoint-url', custom_path + 'cli_eventgrid_event_subscription_resource_get_full_url', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid resource event-subscription delete', custom_path + 'cli_eventgrid_event_subscription_resource_delete', event_subscriptions_factory)
    cli_command(__name__, 'eventgrid resource event-subscription list', custom_path + 'cli_resource_event_subscription_list', event_subscriptions_factory)

    cli_command(__name__, 'eventgrid topic-type list', topic_types_mgmt_path + 'TopicTypesOperations.list', topic_types_factory)
    cli_command(__name__, 'eventgrid topic-type show', topic_types_mgmt_path + 'TopicTypesOperations.get', topic_types_factory)
    cli_command(__name__, 'eventgrid topic-type list-event-types', topic_types_mgmt_path + 'TopicTypesOperations.list_event_types', topic_types_factory)
