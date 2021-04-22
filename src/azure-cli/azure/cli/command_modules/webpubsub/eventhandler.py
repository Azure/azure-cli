# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import json
from azure.mgmt.webpubsub.models import (
    WebPubSubResource,
    EventHandlerSettings
)


def event_handler_list(client, resource_group_name, webpubsub_name):
    resource = client.get(resource_group_name, webpubsub_name)
    return resource.event_handler


def event_handler_update(client, resource_group_name, webpubsub_name, items):
    parsedItem = json.loads(items)
    event_handler = EventHandlerSettings(items=parsedItem)
    parameters = WebPubSubResource(event_handler=event_handler)
    return client.begin_update(resource_group_name, webpubsub_name, parameters)


def event_handler_clear(client, resource_group_name, webpubsub_name):
    event_handler = EventHandlerSettings(items={})
    parameters = WebPubSubResource(event_handler=event_handler)
    return client.begin_update(resource_group_name, webpubsub_name, parameters)


def event_handler_hub_update(client, resource_group_name, webpubsub_name, hub_name, template):
    event_handler = client.get(resource_group_name, webpubsub_name).event_handler
    if event_handler is None or event_handler.items is None:
        event_handler = EventHandlerSettings(items={})
    items = event_handler.items

    items[hub_name] = template
    parameters = WebPubSubResource(event_handler=event_handler)
    print(parameters.event_handler)
    return client.begin_update(resource_group_name, webpubsub_name, parameters)


def event_handler_hub_remove(client, resource_group_name, webpubsub_name, hub_name):
    event_handler = client.get(resource_group_name, webpubsub_name).event_handler
    if event_handler is None or event_handler.items is None:
        event_handler = EventHandlerSettings(items={})
    items = event_handler.items
    items.pop(hub_name, None)
    parameters = WebPubSubResource(event_handler=event_handler)
    return client.begin_update(resource_group_name, webpubsub_name, parameters)
