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
    print(items)
    parsedItem = json.loads(items)
    event_handler = EventHandlerSettings(items=parsedItem)
    parameters = WebPubSubResource(event_handler=event_handler)
    return client.update(parameters, resource_group_name, webpubsub_name)


def event_handler_clear(client, resource_group_name, webpubsub_name):
    event_handler = EventHandlerSettings(items={})
    parameters = WebPubSubResource(event_handler=event_handler)
    return client.update(parameters, resource_group_name, webpubsub_name)
