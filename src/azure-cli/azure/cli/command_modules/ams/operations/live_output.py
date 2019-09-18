# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.media.models import LiveOutput
from knack.util import CLIError


def create_live_output(client, resource_group_name, account_name, live_event_name,
                       live_output_name, asset_name, archive_window_length, manifest_name=None,
                       description=None, fragments_per_ts_segment=None, output_snap_time=None):
    from azure.mgmt.media.models import (Hls)

    if fragments_per_ts_segment is not None:
        fragments_per_ts_segment = Hls(fragments_per_ts_segment=fragments_per_ts_segment)

    return client.create(resource_group_name=resource_group_name, account_name=account_name,
                         live_event_name=live_event_name, live_output_name=live_output_name,
                         parameters=LiveOutput(asset_name=asset_name, manifest_name=manifest_name,
                                               archive_window_length=archive_window_length,
                                               description=description, hls=fragments_per_ts_segment,
                                               output_snap_time=output_snap_time))


def get_live_output(client, resource_group_name, account_name, live_event_name, live_output_name):
    live_output = client.get(resource_group_name, account_name, live_event_name, live_output_name)
    if not live_output:
        raise CLIError('The live-output resource was not found.')

    return live_output
