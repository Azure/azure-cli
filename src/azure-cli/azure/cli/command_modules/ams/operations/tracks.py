# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.core.util import CLIError, sdk_no_wait
from azure.mgmt.media.models import (AssetTrack, TextTrack)


def get_asset_track(client, account_name, resource_group_name, asset_name, track_name):
    return client.get(resource_group_name, account_name, asset_name, track_name)


def create_asset_track(client, account_name, resource_group_name, asset_name, track_name, track_type, file_name=None,
                       display_name=None, player_visibility=None, language_code=None, no_wait=False):
    track = None
    if track_type == 'Text':
        track = TextTrack(file_name=file_name, display_name=display_name, player_visibility=player_visibility,
                          language_code=language_code)
    else:
        raise CLIError("'{}' is not a valid track type. Currently supported track type is Text.".format(track_type))

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name=resource_group_name,
                       account_name=account_name, asset_name=asset_name, track_name=track_name,
                       parameters=AssetTrack(track=track))


def update_track_data(client, account_name, resource_group_name, asset_name, track_name, no_wait=False):
    return sdk_no_wait(no_wait, client.begin_update_track_data, resource_group_name=resource_group_name,
                       account_name=account_name, asset_name=asset_name, track_name=track_name)


def update_track(client, account_name, resource_group_name, asset_name, track_name,
                 display_name=None, player_visibility=None, language_code=None, no_wait=False):
    current_track = client.get(resource_group_name, account_name, asset_name, track_name)

    if display_name:
        current_track.track.display_name = display_name
    if player_visibility:
        current_track.track.player_visibility = player_visibility
    if language_code:
        current_track.track.language_code = language_code

    return sdk_no_wait(no_wait, client.begin_update, resource_group_name=resource_group_name,
                       account_name=account_name, asset_name=asset_name, track_name=track_name,
                       parameters=current_track)
