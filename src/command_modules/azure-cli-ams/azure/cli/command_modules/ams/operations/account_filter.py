# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from knack.util import CLIError

from azure.mgmt.media.models import (AccountFilter, FilterTrackSelection,
                                     FilterTrackPropertyCondition,
                                     PresentationTimeRange, FirstQuality)


def create_account_filter(client, account_name, resource_group_name, filter_name, start_timestamp=None,
                          end_timestamp=None, presentation_window_duration=None, live_backoff_duration=None,
                          timescale=None, force_end_timestamp=False, bitrate=None, tracks=None):

    first_quality = None
    presentation_time_range = None

    if bitrate is not None:
        first_quality = FirstQuality(bitrate=bitrate)

    if any([start_timestamp, end_timestamp, presentation_window_duration,
            live_backoff_duration, timescale]):
        presentation_time_range = PresentationTimeRange(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            presentation_window_duration=presentation_window_duration,
            live_backoff_duration=live_backoff_duration,
            timescale=timescale,
            force_end_timestamp=force_end_timestamp
        )

    account_filter = AccountFilter(tracks=_parse_filter_tracks_json(tracks),
                                   presentation_time_range=presentation_time_range,
                                   first_quality=first_quality)

    return client.create_or_update(resource_group_name, account_name, filter_name,
                                   account_filter)


def update_account_filter(instance, start_timestamp=None, end_timestamp=None,
                          presentation_window_duration=None, live_backoff_duration=None,
                          timescale=None, bitrate=None, tracks=None, force_end_timestamp=None):

    if not instance:
        raise CLIError('The account filter resource was not found.')

    if bitrate:
        instance.first_quality = FirstQuality(bitrate=bitrate)

    if any([start_timestamp, end_timestamp, presentation_window_duration,
            live_backoff_duration, timescale, force_end_timestamp is not None]):

        if instance.presentation_time_range is None:
            if not all([start_timestamp, end_timestamp, presentation_window_duration,
                        live_backoff_duration, timescale, force_end_timestamp is not None]):
                raise CLIError('All parameters related to PresentationTimeRange must be set to create it.')

            instance.presentation_time_range = PresentationTimeRange(
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                presentation_window_duration=presentation_window_duration,
                live_backoff_duration=live_backoff_duration,
                timescale=timescale,
                force_end_timestamp=force_end_timestamp
            )

        else:
            if start_timestamp is not None:
                instance.presentation_time_range.start_timestamp = start_timestamp

            if end_timestamp is not None:
                instance.presentation_time_range.end_timestamp = end_timestamp

            if presentation_window_duration is not None:
                instance.presentation_time_range.presentation_window_duration = presentation_window_duration

            if live_backoff_duration is not None:
                instance.presentation_time_range.live_backoff_duration = live_backoff_duration

            if force_end_timestamp is not None:
                instance.presentation_time_range.force_end_timestamp = force_end_timestamp

            if timescale is not None:
                instance.presentation_time_range.timescale = timescale

    if tracks is not None:
        instance.tracks = _parse_filter_tracks_json(tracks)

    return instance


def _parse_filter_tracks_json(tracks):
    tracks_result = None
    if tracks is not None:
        tracks_result = []
        try:
            tracks_json = json.loads(tracks)
            for track_selection_json in tracks_json:
                track_properties = []
                for track_property_json in track_selection_json.get('trackSelections'):
                    track_property = FilterTrackPropertyCondition(**track_property_json)
                    track_properties.append(track_property)
                tracks_result.append(FilterTrackSelection(track_selections=track_properties))
        except TypeError as ex:
            errorMessage = 'Malformed JSON.'
            raise CLIError('{}. {}'.format(str(ex), errorMessage))
    return tracks_result
