# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from six.moves.urllib.parse import quote  # pylint: disable=import-error
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.tools import parse_resource_id

from azure.cli.core.commands.client_factory import get_subscription_id
from azure.mgmt.eventgrid.models import (
    EventSubscription,
    EventSubscriptionUpdateParameters,
    WebHookEventSubscriptionDestination,
    EventHubEventSubscriptionDestination,
    EventSubscriptionFilter)

logger = get_logger(__name__)

EVENTGRID_NAMESPACE = "Microsoft.EventGrid"
RESOURCES_NAMESPACE = "Microsoft.Resources"
SUBSCRIPTIONS = "subscriptions"
RESOURCE_GROUPS = "resourcegroups"
EVENTGRID_TOPICS = "topics"
WEBHOOK_DESTINATION = "webhook"
EVENTHUB_DESTINATION = "eventhub"


def cli_topic_list(
        client,
        resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list_by_subscription()


def cli_eventgrid_event_subscription_create(
        cmd,
        client,
        event_subscription_name,
        endpoint,
        resource_id=None,
        resource_group_name=None,
        topic_name=None,
        endpoint_type=WEBHOOK_DESTINATION,
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        labels=None):
    scope = _get_scope_for_event_subscription(cmd.cli_ctx, resource_id, topic_name, resource_group_name)

    if endpoint_type.lower() == WEBHOOK_DESTINATION.lower():
        destination = WebHookEventSubscriptionDestination(endpoint)
    elif endpoint_type.lower() == EVENTHUB_DESTINATION.lower():
        destination = EventHubEventSubscriptionDestination(endpoint)

    event_subscription_filter = EventSubscriptionFilter(
        subject_begins_with,
        subject_ends_with,
        included_event_types,
        is_subject_case_sensitive)
    event_subscription_info = EventSubscription(destination, event_subscription_filter, labels)

    async_event_subscription_create = client.create_or_update(
        scope,
        event_subscription_name,
        event_subscription_info)
    created_event_subscription = async_event_subscription_create.result()
    return created_event_subscription


def event_subscription_setter(
        cmd,
        client,
        parameters,
        event_subscription_name,
        resource_id=None,
        resource_group_name=None,
        topic_name=None):
    scope = _get_scope_for_event_subscription(cmd.cli_ctx, resource_id, topic_name, resource_group_name)

    async_event_subscription_update = client.update(
        scope,
        event_subscription_name,
        parameters)
    updated_event_subscription = async_event_subscription_update.result()
    return updated_event_subscription


def cli_eventgrid_event_subscription_get(
        cmd,
        client,
        event_subscription_name,
        resource_id=None,
        resource_group_name=None,
        topic_name=None,
        include_full_endpoint_url=False):
    scope = _get_scope_for_event_subscription(cmd.cli_ctx, resource_id, topic_name, resource_group_name)
    retrieved_event_subscription = client.get(scope, event_subscription_name)
    destination = retrieved_event_subscription.destination
    if include_full_endpoint_url and isinstance(destination, WebHookEventSubscriptionDestination):
        full_endpoint_url = client.get_full_url(scope, event_subscription_name)
        destination.endpoint_url = full_endpoint_url.endpoint_url

    return retrieved_event_subscription


def cli_eventgrid_event_subscription_delete(
        cmd,
        client,
        event_subscription_name,
        resource_id=None,
        resource_group_name=None,
        topic_name=None):
    scope = _get_scope_for_event_subscription(cmd.cli_ctx, resource_id, topic_name, resource_group_name)
    client.delete(scope, event_subscription_name)


def cli_event_subscription_list(   # pylint: disable=too-many-return-statements
        client,
        resource_id=None,
        resource_group_name=None,
        topic_name=None,
        location=None,
        topic_type_name=None):
    if resource_id:
        # Resource ID is specified, we need to list only for the particular resource.
        if resource_group_name is not None or topic_name is not None:
            raise CLIError('Since ResourceId is specified, topic-name and resource-group-name should not be specified.')

        id_parts = parse_resource_id(resource_id)
        rg_name = id_parts['resource_group']
        resource_name = id_parts['name']
        provider_namespace = id_parts['namespace']
        resource_type = id_parts['resource_type']

        return client.list_by_resource(
            rg_name,
            provider_namespace,
            resource_type,
            resource_name)

    if topic_name:
        if resource_group_name is None:
            raise CLIError('Since topic-name is specified, resource-group-name must also be specified.')

        return client.list_by_resource(
            resource_group_name,
            EVENTGRID_NAMESPACE,
            EVENTGRID_TOPICS,
            topic_name)

    if topic_type_name:
        if location:
            if resource_group_name:
                return client.list_regional_by_resource_group_for_topic_type(
                    resource_group_name,
                    location,
                    topic_type_name)

            return client.list_regional_by_subscription_for_topic_type(
                location,
                topic_type_name)

        if resource_group_name:
            return client.list_global_by_resource_group_for_topic_type(
                resource_group_name,
                topic_type_name)

        return client.list_global_by_subscription_for_topic_type(topic_type_name)

    if location:
        if resource_group_name:
            return client.list_regional_by_resource_group(
                resource_group_name,
                location)

        return client.list_regional_by_subscription(location)

    if resource_group_name:
        return client.list_global_by_resource_group(resource_group_name)

    return client.list_global_by_subscription()


def _get_scope(
        cli_ctx,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name):
    subscription_id = get_subscription_id(cli_ctx)

    if provider_namespace == RESOURCES_NAMESPACE:
        if resource_group_name:
            scope = (
                '/subscriptions/{}/resourceGroups/{}'
                .format(quote(subscription_id),
                        quote(resource_group_name)))
        else:
            scope = (
                '/subscriptions/{}'
                .format(quote(subscription_id)))
    else:
        scope = (
            '/subscriptions/{}/resourceGroups/{}/providers/{}/{}/{}'
            .format(quote(subscription_id),
                    quote(resource_group_name),
                    quote(provider_namespace),
                    quote(resource_type),
                    quote(resource_name)))

    return scope


def _get_scope_for_event_subscription(
        cli_ctx,
        resource_id,
        topic_name,
        resource_group_name):
    if resource_id:
        # Resource ID is provided, use that as the scope for the event subscription.
        scope = resource_id
    elif topic_name:
        # Topic name is provided, use the topic and resource group to build a scope for the user topic
        if resource_group_name is None:
            raise CLIError("When topic name is specified, the resource group name must also be specified.")

        scope = _get_scope(cli_ctx, resource_group_name, EVENTGRID_NAMESPACE, EVENTGRID_TOPICS, topic_name)
    elif resource_group_name:
        # Event subscription to a resource group.
        scope = _get_scope(cli_ctx, resource_group_name, RESOURCES_NAMESPACE, RESOURCE_GROUPS, resource_group_name)
    else:
        scope = _get_scope(cli_ctx, None, RESOURCES_NAMESPACE, SUBSCRIPTIONS, get_subscription_id(cli_ctx))

    return scope


def event_subscription_getter(
        cmd,
        client,
        event_subscription_name,
        resource_id=None,
        resource_group_name=None,
        topic_name=None):
    scope = _get_scope_for_event_subscription(cmd.cli_ctx, resource_id, topic_name, resource_group_name)
    retrieved_event_subscription = client.get(scope, event_subscription_name)
    return retrieved_event_subscription


def update_event_subscription(
        instance,
        endpoint=None,
        endpoint_type=WEBHOOK_DESTINATION,
        subject_begins_with=None,
        subject_ends_with=None,
        included_event_types=None,
        labels=None):
    event_subscription_destination = None
    event_subscription_labels = instance.labels
    event_subscription_filter = instance.filter

    if endpoint is not None:
        if endpoint_type.lower() == WEBHOOK_DESTINATION.lower():
            event_subscription_destination = WebHookEventSubscriptionDestination(endpoint)
        elif endpoint_type.lower() == EVENTHUB_DESTINATION.lower():
            event_subscription_destination = EventHubEventSubscriptionDestination(endpoint)

    if subject_begins_with is not None:
        event_subscription_filter.subject_begins_with = subject_begins_with

    if subject_ends_with is not None:
        event_subscription_filter.subject_ends_with = subject_ends_with

    if included_event_types is not None:
        event_subscription_filter.included_event_types = included_event_types

    if labels is not None:
        event_subscription_labels = labels

    params = EventSubscriptionUpdateParameters(
        destination=event_subscription_destination,
        filter=event_subscription_filter,
        labels=event_subscription_labels
    )

    return params
