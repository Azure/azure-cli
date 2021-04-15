# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.webpubsub.models import (
    ResourceSku,
    WebPubSubResource
)


def webpubsub_create(client, resource_group_name, webpubsub_name, sku, unit_count=1, location=None, tags=None):
    sku = ResourceSku(name=sku, capacity=unit_count)
    parameter = WebPubSubResource(
        sku=sku,
        location=location,
        tags=tags
    )

    return client.create_or_update(parameter, resource_group_name, webpubsub_name)

def webpubsub_list(client, resource_group_name=None):
    if not resource_group_name:
        return client.list_by_subscription()
    return client.list_by_resource_group(resource_group_name)

def webpubsub_delete(client, webpubsub_name, resource_group_name):
    return client.delete(resource_group_name, webpubsub_name)

def webpubsub_show(client, webpubsub_name, resource_group_name):
    return client.get(resource_group_name, webpubsub_name)

def webpubsub_restart(client, webpubsub_name, resource_group_name):
    return client.restart(resource_group_name, webpubsub_name)

def webpubsub_get():
    return WebPubSubResource()

def webpubsub_set(client, webpubsub_name, resource_group_name, parameters):
    return client.update(parameters, resource_group_name, webpubsub_name)

def update_webpubsub(instance, tags=None, sku=None, unit_count=1):
    if sku is not None:
        instance.sku = ResourceSku(name=sku, capacity=unit_count)

    if tags is not None:
        instance.tags = tags

    return instance
