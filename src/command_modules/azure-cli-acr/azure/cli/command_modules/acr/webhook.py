# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError

from azure.mgmt.containerregistry.v2018_02_01_preview.models import (
    WebhookCreateParameters,
    WebhookUpdateParameters
)

from ._utils import (
    get_resource_group_name_by_registry_name,
    validate_managed_registry
)


WEBHOOKS_NOT_SUPPORTED = 'Webhooks are only supported for managed registries.'


def acr_webhook_list(cmd, client, registry_name, resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    return client.list(resource_group_name, registry_name)


def acr_webhook_create(cmd,
                       client,
                       webhook_name,
                       uri,
                       actions,
                       registry_name,
                       location=None,
                       resource_group_name=None,
                       headers=None,
                       status='enabled',
                       scope=None,
                       tags=None):
    registry, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)

    from msrest.exceptions import ValidationError
    try:
        return client.create(
            resource_group_name,
            registry_name,
            webhook_name,
            WebhookCreateParameters(
                location=location or registry.location,
                service_uri=uri,
                actions=actions,
                custom_headers=headers,
                status=status,
                scope=scope,
                tags=tags
            )
        )
    except ValidationError as e:
        raise CLIError(e)


def acr_webhook_delete(cmd,
                       client,
                       webhook_name,
                       registry_name,
                       resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    return client.delete(resource_group_name, registry_name, webhook_name)


def acr_webhook_show(cmd,
                     client,
                     webhook_name,
                     registry_name,
                     resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
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


def acr_webhook_update_get(client):  # pylint: disable=unused-argument
    """Returns an empty WebhookUpdateParameters object.
    """
    return WebhookUpdateParameters()


def acr_webhook_update_set(cmd,
                           client,
                           webhook_name,
                           registry_name,
                           resource_group_name=None,
                           parameters=None):
    resource_group_name = get_resource_group_name_by_registry_name(
        cmd.cli_ctx, registry_name, resource_group_name)
    return client.update(resource_group_name, registry_name, webhook_name, parameters)


def acr_webhook_get_config(cmd,
                           client,
                           webhook_name,
                           registry_name,
                           resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    return client.get_callback_config(resource_group_name, registry_name, webhook_name)


def acr_webhook_list_events(cmd,
                            client,
                            webhook_name,
                            registry_name,
                            resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    return client.list_events(resource_group_name, registry_name, webhook_name)


def acr_webhook_ping(cmd,
                     client,
                     webhook_name,
                     registry_name,
                     resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, WEBHOOKS_NOT_SUPPORTED)
    return client.ping(resource_group_name, registry_name, webhook_name)
