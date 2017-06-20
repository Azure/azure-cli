# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.containerregistry.v2017_06_01_preview.models import (
    WebhookCreateParameters,
    WebhookUpdateParameters
)

from ._constants import WEBHOOK_API_VERSION
from ._factory import get_acr_service_client
from ._utils import (
    get_resource_group_name_by_registry_name,
    registry_sku_validation
)


WEBHOOKS_NOT_SUPPORTED = 'Webhooks are not supported for registries in Basic SKU.'


def acr_webhook_list(registry_name, resource_group_name=None):
    """Lists all the webhooks for the specified container registry."
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = registry_sku_validation(
        registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    client = get_acr_service_client(WEBHOOK_API_VERSION).webhooks

    return client.list(resource_group_name, registry_name)


def acr_webhook_create(webhook_name,
                       uri,
                       actions,
                       registry_name,
                       resource_group_name=None,
                       headers=None,
                       status='enabled',
                       scope=None,
                       tags=None):
    """Creates a webhook for a container registry.
    :param str webhook_name: The name of webhook
    :param str uri: The service URI for the webhook to post notifications
    :param str actions: The list of actions that trigger the webhook to post notifications
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str headers: Custom headers that will be added to the webhook notifications
    :param str status: Indicates whether the webhook is enabled
    :param str scope: The scope of repositories where the event can be triggered
    """
    arm_registry, resource_group_name = registry_sku_validation(
        registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    location = arm_registry.location

    client = get_acr_service_client(WEBHOOK_API_VERSION).webhooks

    return client.create(
        resource_group_name,
        registry_name,
        webhook_name,
        WebhookCreateParameters(
            location=location,
            service_uri=uri,
            actions=actions,
            custom_headers=headers,
            status=status,
            scope=scope,
            tags=tags
        )
    )


def acr_webhook_delete(webhook_name,
                       registry_name,
                       resource_group_name=None):
    """Deletes a webhook from a container registry.
    :param str webhook_name: The name of webhook
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = registry_sku_validation(
        registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    client = get_acr_service_client(WEBHOOK_API_VERSION).webhooks

    return client.delete(resource_group_name, registry_name, webhook_name)


def acr_webhook_show(webhook_name,
                     registry_name,
                     resource_group_name=None):
    """Gets the properties of the specified webhook.
    :param str webhook_name: The name of webhook
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = registry_sku_validation(
        registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    client = get_acr_service_client(WEBHOOK_API_VERSION).webhooks

    return client.get(resource_group_name, registry_name, webhook_name)


def acr_webhook_update_custom(instance,
                              uri=None,
                              actions=None,
                              headers=None,
                              status=None,
                              scope=None,
                              tags=None):
    if uri is not None:
        instance.service_uri = uri

    if actions is not None:
        instance.actions = actions

    if headers is not None:
        instance.custom_headers = headers

    if status is not None:
        instance.status = status

    if scope is not None:
        instance.scope = scope

    if tags is not None:
        instance.tags = tags

    return instance


def acr_webhook_update_get(client,
                           webhook_name,
                           registry_name,
                           resource_group_name=None):
    """Gets the properties of the specified webhook.
    :param str webhook_name: The name of webhook
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = registry_sku_validation(
        registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)

    webhook = client.get(resource_group_name, registry_name, webhook_name)

    return WebhookUpdateParameters(
        tags=webhook.tags,
        status=webhook.status,
        scope=webhook.scope,
        actions=webhook.actions)


def acr_webhook_update_set(client,
                           webhook_name,
                           registry_name,
                           resource_group_name=None,
                           parameters=None):
    """Sets the properties of the specified webhook.
    :param str webhook_name: The name of webhook
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param WebhookUpdateParameters parameters: The webhook update parameters object
    """
    resource_group_name = get_resource_group_name_by_registry_name(
        registry_name, resource_group_name)

    return client.update(resource_group_name, registry_name, webhook_name, parameters)


def acr_webhook_get_config(webhook_name,
                           registry_name,
                           resource_group_name=None):
    """Gets the configuration of service URI and custom headers for the webhook.
    :param str webhook_name: The name of webhook
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = registry_sku_validation(
        registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    client = get_acr_service_client(WEBHOOK_API_VERSION).webhooks

    return client.get_callback_config(resource_group_name, registry_name, webhook_name)


def acr_webhook_list_events(webhook_name,
                            registry_name,
                            resource_group_name=None):
    """Lists recent events for the specified webhook.
    :param str webhook_name: The name of webhook
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = registry_sku_validation(
        registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    client = get_acr_service_client(WEBHOOK_API_VERSION).webhooks

    return client.list_events(resource_group_name, registry_name, webhook_name)


def acr_webhook_ping(webhook_name,
                     registry_name,
                     resource_group_name=None):
    """Triggers a ping event to be sent to the webhook.
    :param str webhook_name: The name of webhook
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = registry_sku_validation(
        registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    client = get_acr_service_client(WEBHOOK_API_VERSION).webhooks

    return client.ping(resource_group_name, registry_name, webhook_name)
