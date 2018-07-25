# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create(client, resource_group_name, account_name, name, parameters, location):
    from azure.mgmt.media.models import LiveEventInputProtocol
    from azure.mgmt.media.models import LiveEventInput
    from azure.mgmt.media.models import LiveEvent

    protocol = LiveEventInputProtocol(parameters)
    liveeventinput = LiveEventInput(streaming_protocol=protocol)
    live_event = LiveEvent(input=liveeventinput, location=location)

    return client.create(resource_group_name=resource_group_name, account_name=account_name,
                         live_event_name=name, parameters=live_event)
