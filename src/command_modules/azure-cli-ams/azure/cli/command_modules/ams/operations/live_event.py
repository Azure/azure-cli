# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create(client, resource_group_name, account_name, live_event_name, streaming_protocol, location,
           auto_start=False, encoding_type=None, preset_name=None, tags=None, description=None):
    from azure.mgmt.media.models import LiveEventInputProtocol
    from azure.mgmt.media.models import LiveEventInput
    from azure.mgmt.media.models import LiveEvent
    from azure.mgmt.media.models import LiveEventEncodingType
    from azure.mgmt.media.models import LiveEventEncoding

    protocol = LiveEventInputProtocol(streaming_protocol)
    liveeventinput = LiveEventInput(streaming_protocol=protocol)
    encodingtypeenum = LiveEventEncodingType(encoding_type)
    liveeventencoding = LiveEventEncoding(encoding_type=encodingtypeenum, preset_name=preset_name)

    live_event = LiveEvent(input=liveeventinput, location=location, encoding=liveeventencoding)

    return client.create(resource_group_name=resource_group_name, account_name=account_name,
                         live_event_name=live_event_name, parameters=live_event, auto_start=auto_start,
                         description=description, tags=tags)
