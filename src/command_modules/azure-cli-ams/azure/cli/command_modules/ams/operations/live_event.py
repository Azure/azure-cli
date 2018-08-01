# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import sdk_no_wait
from azure.cli.core.commands import LongRunningOperation


def create(client, resource_group_name, account_name, live_event_name, streaming_protocol, location,
           auto_start=False, encoding_type=None, preset_name=None, tags=None, description=None,
           key_frame_interval_duration=None, access_token=None, no_wait=False):
    from azure.mgmt.media.models import LiveEventInputProtocol
    from azure.mgmt.media.models import LiveEventInput
    from azure.mgmt.media.models import LiveEvent
    from azure.mgmt.media.models import LiveEventEncoding

    protocol = LiveEventInputProtocol(streaming_protocol)
    live_event_input = LiveEventInput(streaming_protocol=protocol, access_token=access_token,
                                      key_frame_interval_duration=key_frame_interval_duration)

    live_event_encoding = LiveEventEncoding(encoding_type=encoding_type, preset_name=preset_name)

    live_event = LiveEvent(input=live_event_input, location=location, encoding=live_event_encoding)

    return sdk_no_wait(no_wait, client.create, resource_group_name=resource_group_name, account_name=account_name,
                       live_event_name=live_event_name, parameters=live_event, auto_start=auto_start,
                       description=description, tags=tags, key_frame_interval_duration=key_frame_interval_duration,
                       access_token=access_token)


def start(cmd, client, resource_group_name, account_name, live_event_name, no_wait=False):
    if no_wait:
        return sdk_no_wait(no_wait, client.start, resource_group_name, account_name, live_event_name)

    LongRunningOperation(cmd.cli_ctx)(client.start(resource_group_name, account_name, live_event_name))

    return client.get(resource_group_name, account_name, live_event_name)


def stop(cmd, client, resource_group_name, account_name, live_event_name,
         remove_outputs_on_stop=False, no_wait=False):

    if no_wait:
        return sdk_no_wait(no_wait, client.stop, resource_group_name, account_name, live_event_name,
                           remove_outputs_on_stop)

    LongRunningOperation(cmd.cli_ctx)(client.stop(resource_group_name, account_name, live_event_name,
                                                  remove_outputs_on_stop))

    return client.get(resource_group_name, account_name, live_event_name)
