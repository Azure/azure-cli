# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.core.azlogging as azlogging
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.mgmt.eventgrid.models import (
    EventSubscription,
    WebHookEventSubscriptionDestination,
    EventHubEventSubscriptionDestination,
    EventSubscriptionFilter)

from six.moves.urllib.parse import quote  # pylint: disable=import-error

logger = azlogging.get_az_logger(__name__)
EVENTGRID_NAMESPACE = "Microsoft.EventGrid"
RESOURCES_NAMESPACE = "Microsoft.Resources"
RESOURCE_TYPE_SUBSCRIPTIONS = "subscriptions"
RESOURCE_TYPE_RESOURCE_GROUPS = "resourcegroups"
EVENTGRID_TOPICS = "topics"
WEBHOOK_DESTINATION = "webhook"
EVENTHUB_DESTINATION = "eventhub"


def cli_topic_list(
        client,
        resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list_by_subscription()


def cli_eventgrid_event_subscription_topic_create(
        client,
        resource_group_name,
        topic_name,
        event_subscription_name,
        endpoint,
        endpoint_type="WebHook",
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        labels=None):
    return _event_subscription_create(
        client,
        resource_group_name,
        EVENTGRID_NAMESPACE,
        EVENTGRID_TOPICS,
        topic_name,
        event_subscription_name,
        endpoint,
        endpoint_type,
        included_event_types,
        subject_begins_with,
        subject_ends_with,
        is_subject_case_sensitive,
        labels)


def cli_eventgrid_event_subscription_topic_get(
        client,
        resource_group_name,
        topic_name,
        event_subscription_name):
    return _event_subscription_get(
        client,
        resource_group_name,
        EVENTGRID_NAMESPACE,
        EVENTGRID_TOPICS,
        topic_name,
        event_subscription_name)


def cli_eventgrid_event_subscription_topic_get_full_url(
        client,
        resource_group_name,
        topic_name,
        event_subscription_name):
    return _event_subscription_get_full_url(
        client,
        resource_group_name,
        EVENTGRID_NAMESPACE,
        EVENTGRID_TOPICS,
        topic_name,
        event_subscription_name)


def cli_eventgrid_event_subscription_topic_delete(
        client,
        resource_group_name,
        topic_name,
        event_subscription_name):
    _event_subscription_delete(
        client,
        resource_group_name,
        EVENTGRID_NAMESPACE,
        EVENTGRID_TOPICS,
        topic_name,
        event_subscription_name)


def cli_eventgrid_event_subscription_resource_create(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name,
        endpoint,
        endpoint_type="WebHook",
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        labels=None):
    return _event_subscription_create(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name,
        endpoint,
        endpoint_type,
        included_event_types,
        subject_begins_with,
        subject_ends_with,
        is_subject_case_sensitive,
        labels)


def cli_eventgrid_event_subscription_resource_get(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name):
    return _event_subscription_get(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name)


def cli_eventgrid_event_subscription_resource_get_full_url(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name):
    return _event_subscription_get_full_url(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name)


def cli_eventgrid_event_subscription_resource_delete(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name):
    _event_subscription_delete(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name)


def cli_eventgrid_event_subscription_arm_create(
        client,
        event_subscription_name,
        endpoint,
        resource_group_name=None,
        endpoint_type="WebHook",
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        labels=None):
    resource_type, resource_name = _get_arm_resource_info(resource_group_name)

    return _event_subscription_create(
        client,
        resource_group_name,
        RESOURCES_NAMESPACE,
        resource_type,
        resource_name,
        event_subscription_name,
        endpoint,
        endpoint_type,
        included_event_types,
        subject_begins_with,
        subject_ends_with,
        is_subject_case_sensitive,
        labels)


def cli_eventgrid_event_subscription_arm_get(
        client,
        event_subscription_name,
        resource_group_name=None):
    resource_type, resource_name = _get_arm_resource_info(resource_group_name)

    return _event_subscription_get(
        client,
        resource_group_name,
        RESOURCES_NAMESPACE,
        resource_type,
        resource_name,
        event_subscription_name)


def cli_eventgrid_event_subscription_arm_get_full_url(
        client,
        event_subscription_name,
        resource_group_name=None):
    resource_type, resource_name = _get_arm_resource_info(resource_group_name)

    return _event_subscription_get_full_url(
        client,
        resource_group_name,
        RESOURCES_NAMESPACE,
        resource_type,
        resource_name,
        event_subscription_name)


def cli_eventgrid_event_subscription_arm_delete(
        client,
        event_subscription_name,
        resource_group_name=None):
    resource_type, resource_name = _get_arm_resource_info(resource_group_name)

    _event_subscription_delete(
        client,
        resource_group_name,
        RESOURCES_NAMESPACE,
        resource_type,
        resource_name,
        event_subscription_name)


def cli_topic_event_subscription_list(
        client,
        resource_group_name,
        topic_name):
    return resource_event_subscription_list_internal(
        client,
        resource_group_name,
        EVENTGRID_NAMESPACE,
        EVENTGRID_TOPICS,
        topic_name)


def cli_resource_event_subscription_list(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name):
    return resource_event_subscription_list_internal(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name)


def cli_event_subscription_list(   # pylint: disable=too-many-return-statements
        client,
        resource_group_name=None,
        location=None,
        topic_type_name=None):
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


def resource_event_subscription_list_internal(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name):
    return client.list_by_resource(
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name)


def _event_subscription_create(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name,
        endpoint,
        endpoint_type,
        included_event_types,
        subject_begins_with,
        subject_ends_with,
        is_subject_case_sensitive,
        labels):
    scope = _get_scope(resource_group_name, provider_namespace, resource_type, resource_name)
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

    async_event_subscription_create = client.create(
        scope,
        event_subscription_name,
        event_subscription_info)
    created_event_subscription = async_event_subscription_create.result()
    return created_event_subscription


def _event_subscription_get(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name):
    scope = _get_scope(resource_group_name, provider_namespace, resource_type, resource_name)
    retrieved_event_subscription = client.get(scope, event_subscription_name)
    return retrieved_event_subscription


def _event_subscription_get_full_url(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name):
    scope = _get_scope(resource_group_name, provider_namespace, resource_type, resource_name)
    full_endpoint_url = client.get_full_url(scope, event_subscription_name)
    return full_endpoint_url


def _event_subscription_delete(
        client,
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name,
        event_subscription_name):
    scope = _get_scope(resource_group_name, provider_namespace, resource_type, resource_name)
    client.delete(scope, event_subscription_name)


def _get_scope(
        resource_group_name,
        provider_namespace,
        resource_type,
        resource_name):
    subscription_id = get_subscription_id()

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


def _get_arm_resource_info(resource_group_name):
    if resource_group_name:
        resource_type = RESOURCE_TYPE_RESOURCE_GROUPS
        resource_name = resource_group_name
    else:
        resource_type = RESOURCE_TYPE_SUBSCRIPTIONS
        resource_name = get_subscription_id()

    return resource_type, resource_name
