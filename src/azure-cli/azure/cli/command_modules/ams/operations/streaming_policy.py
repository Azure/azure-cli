# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from azure.cli.core.util import CLIError
from azure.cli.command_modules.ams._client_factory import get_streaming_policies_client
from azure.cli.command_modules.ams._utils import show_resource_not_found_message
from azure.mgmt.media.models import (StreamingPolicy, NoEncryption,
                                     CommonEncryptionCenc, TrackSelection, TrackPropertyCondition,
                                     StreamingPolicyContentKeys, DefaultKey, StreamingPolicyContentKey,
                                     CbcsDrmConfiguration, CommonEncryptionCbcs,
                                     CencDrmConfiguration, StreamingPolicyPlayReadyConfiguration,
                                     StreamingPolicyWidevineConfiguration, EnabledProtocols,
                                     EnvelopeEncryption, StreamingPolicyFairPlayConfiguration)


def create_streaming_policy(cmd,  # pylint: disable=too-many-locals
                            resource_group_name,
                            account_name,
                            streaming_policy_name,
                            no_encryption_protocols=None,
                            default_content_key_policy_name=None,
                            cbcs_clear_tracks=None,
                            cbcs_default_key_label=None,
                            cbcs_default_key_policy_name=None,
                            cbcs_key_to_track_mappings=None,
                            cbcs_protocols=None,
                            cbcs_play_ready_template=None,
                            cbcs_play_ready_attributes=None,
                            cbcs_widevine_template=None,
                            cbcs_fair_play_template=None,
                            cbcs_fair_play_allow_persistent_license=False,
                            cenc_default_key_label=None,
                            cenc_default_key_policy_name=None,
                            cenc_clear_tracks=None,
                            cenc_key_to_track_mappings=None,
                            cenc_disable_play_ready=None,
                            cenc_play_ready_template=None,
                            cenc_play_ready_attributes=None,
                            cenc_disable_widevine=None,
                            cenc_widevine_template=None,
                            cenc_protocols=None,
                            envelope_clear_tracks=None,
                            envelope_default_key_label=None,
                            envelope_default_key_policy_name=None,
                            envelope_key_to_track_mappings=None,
                            envelope_protocols=None,
                            envelope_template=None):

    envelope_encryption = None
    if any([envelope_protocols, envelope_clear_tracks, envelope_template,
            envelope_default_key_label, envelope_default_key_policy_name, envelope_key_to_track_mappings]):
        envelope_encryption = _envelope_encryption_factory(envelope_clear_tracks,
                                                           envelope_default_key_label,
                                                           envelope_default_key_policy_name,
                                                           envelope_key_to_track_mappings,
                                                           envelope_protocols,
                                                           envelope_template)

    common_encryption_cenc = None
    if any([cenc_protocols, cenc_widevine_template, cenc_default_key_label, cenc_default_key_policy_name,
            cenc_key_to_track_mappings, cenc_clear_tracks, cenc_play_ready_template, cenc_play_ready_attributes]):
        common_encryption_cenc = _cenc_encryption_factory(cenc_clear_tracks,
                                                          cenc_default_key_label,
                                                          cenc_default_key_policy_name,
                                                          cenc_disable_play_ready,
                                                          cenc_disable_widevine,
                                                          cenc_key_to_track_mappings,
                                                          cenc_play_ready_attributes,
                                                          cenc_play_ready_template,
                                                          cenc_protocols,
                                                          cenc_widevine_template)

    common_encryption_cbcs = None
    if any([cbcs_clear_tracks,
            cbcs_default_key_label,
            cbcs_default_key_policy_name,
            cbcs_fair_play_template,
            cbcs_fair_play_allow_persistent_license,
            cbcs_key_to_track_mappings,
            cbcs_play_ready_template,
            cbcs_play_ready_attributes,
            cbcs_widevine_template,
            cbcs_protocols]):
        common_encryption_cbcs = _cbcs_encryption_factory(cbcs_clear_tracks,
                                                          cbcs_default_key_label,
                                                          cbcs_default_key_policy_name,
                                                          cbcs_fair_play_template,
                                                          cbcs_fair_play_allow_persistent_license,
                                                          cbcs_key_to_track_mappings,
                                                          cbcs_play_ready_template,
                                                          cbcs_play_ready_attributes,
                                                          cbcs_widevine_template,
                                                          cbcs_protocols)

    no_encryption = None
    if not any([envelope_encryption, common_encryption_cenc, common_encryption_cbcs]) or no_encryption_protocols:
        no_encryption = _no_encryption_factory(no_encryption_protocols)

    streaming_policy = StreamingPolicy(default_content_key_policy_name=default_content_key_policy_name,
                                       no_encryption=no_encryption,
                                       envelope_encryption=envelope_encryption,
                                       common_encryption_cenc=common_encryption_cenc,
                                       common_encryption_cbcs=common_encryption_cbcs)

    return get_streaming_policies_client(cmd.cli_ctx).create(resource_group_name, account_name,
                                                             streaming_policy_name, streaming_policy)


def _no_encryption_factory(no_encryption_protocols):
    enabled_protocols = _build_enabled_protocols_object(no_encryption_protocols)
    return NoEncryption(enabled_protocols=enabled_protocols)


def _cenc_encryption_factory(cenc_clear_tracks,
                             cenc_default_key_label,
                             cenc_default_key_policy_name,
                             cenc_disable_play_ready,
                             cenc_disable_widevine,
                             cenc_key_to_track_mappings,
                             cenc_play_ready_attributes,
                             cenc_play_ready_template,
                             cenc_protocols,
                             cenc_widevine_template):
    cenc_enabled_protocols = _build_enabled_protocols_object(cenc_protocols)

    if cenc_disable_play_ready and cenc_disable_widevine:
        message = '--cenc-disable-play-ready and --cenc-disable-widevine cannot both be specified'
        raise ValueError(message)

    cenc_play_ready_config = None
    if not cenc_disable_play_ready:
        if cenc_play_ready_template or cenc_play_ready_attributes:
            cenc_play_ready_config = StreamingPolicyPlayReadyConfiguration(
                custom_license_acquisition_url_template=cenc_play_ready_template,
                play_ready_custom_attributes=cenc_play_ready_attributes)
        else:
            cenc_play_ready_config = StreamingPolicyPlayReadyConfiguration()

    cenc_widevine_config = None
    if not cenc_disable_widevine:
        if cenc_widevine_template:
            cenc_widevine_config = StreamingPolicyWidevineConfiguration(
                custom_license_acquisition_url_template=cenc_widevine_template)
        else:
            cenc_widevine_config = StreamingPolicyWidevineConfiguration()

    key_to_track_mappings = _parse_key_to_track_mappings_json(cenc_key_to_track_mappings)
    cenc_content_keys = StreamingPolicyContentKeys(default_key=DefaultKey(label=cenc_default_key_label,
                                                                          policy_name=cenc_default_key_policy_name),
                                                   key_to_track_mappings=key_to_track_mappings)

    return CommonEncryptionCenc(enabled_protocols=cenc_enabled_protocols,
                                clear_tracks=_parse_clear_tracks_json(cenc_clear_tracks),
                                content_keys=cenc_content_keys,
                                drm=CencDrmConfiguration(play_ready=cenc_play_ready_config,
                                                         widevine=cenc_widevine_config))


def _cbcs_encryption_factory(cbcs_clear_tracks,
                             cbcs_default_key_label,
                             cbcs_default_key_policy_name,
                             cbcs_fair_play_template,
                             cbcs_fair_play_allow_persistent_license,
                             cbcs_key_to_track_mappings,
                             cbcs_play_ready_template,
                             cbcs_play_ready_attributes,
                             cbcs_widevine_template,
                             cbcs_protocols):
    cbcs_enabled_protocols = _build_enabled_protocols_object(cbcs_protocols)

    cbcs_play_ready_config = None
    if cbcs_play_ready_template or cbcs_play_ready_attributes:
        cbcs_play_ready_config = StreamingPolicyPlayReadyConfiguration(
            play_ready_custom_attributes=cbcs_play_ready_attributes,
            custom_license_acquisition_url_template=cbcs_play_ready_template)

    cbcs_widevine_config = None
    if cbcs_widevine_template:
        cbcs_widevine_config = StreamingPolicyWidevineConfiguration(
            custom_license_acquisition_url_template=cbcs_widevine_template)

    cbcs_fair_play_config = StreamingPolicyFairPlayConfiguration(
        allow_persistent_license=cbcs_fair_play_allow_persistent_license,
        custom_license_acquisition_url_template=cbcs_fair_play_template)

    cbcs_content_keys = StreamingPolicyContentKeys(
        default_key=DefaultKey(label=cbcs_default_key_label,
                               policy_name=cbcs_default_key_policy_name),
        key_to_track_mappings=_parse_key_to_track_mappings_json(cbcs_key_to_track_mappings))

    return CommonEncryptionCbcs(
        enabled_protocols=cbcs_enabled_protocols,
        clear_tracks=_parse_clear_tracks_json(cbcs_clear_tracks),
        content_keys=cbcs_content_keys,
        drm=CbcsDrmConfiguration(play_ready=cbcs_play_ready_config,
                                 widevine=cbcs_widevine_config,
                                 fair_play=cbcs_fair_play_config))


def _parse_key_to_track_mappings_json(key_to_track_mappings):
    key_to_track_mappings_result = None
    if key_to_track_mappings is not None:
        key_to_track_mappings_result = []
        key_to_track_mappings_json = json.loads(key_to_track_mappings)
        for str_policy_content_key_json in key_to_track_mappings_json:
            str_policy_content_key = StreamingPolicyContentKey(**str_policy_content_key_json)
            str_policy_content_key.policy_name = str_policy_content_key_json.get('policyName')
            key_to_track_mappings_result.append(str_policy_content_key)
    return key_to_track_mappings_result


def _parse_clear_tracks_json(clear_tracks):
    clear_tracks_result = None
    if clear_tracks is not None:
        clear_tracks_result = []
        try:
            clear_tracks_json = json.loads(clear_tracks)
            for track_selection_json in clear_tracks_json:
                track_properties = []
                for track_property_json in track_selection_json.get('trackSelections'):
                    track_property = TrackPropertyCondition(**track_property_json)
                    track_properties.append(track_property)
                clear_tracks_result.append(TrackSelection(track_selections=track_properties))
        except TypeError as ex:
            errorMessage = 'For further information on how to build the JSON ' \
                'containing a list of TrackSelection, please refer to ' \
                'https://docs.microsoft.com/en-us/rest/api/media/streamingpolicies/create#trackselection'
            raise CLIError('{}. {}'.format(str(ex), errorMessage))
    return clear_tracks_result


def _build_enabled_protocols_object(protocols):
    if protocols is None:
        protocols = []

    return EnabledProtocols(download='Download' in protocols,
                            dash='Dash' in protocols,
                            hls='HLS' in protocols,
                            smooth_streaming='SmoothStreaming' in protocols)


def _envelope_encryption_factory(envelope_clear_tracks,
                                 envelope_default_key_label,
                                 envelope_default_key_policy_name,
                                 envelope_key_to_track_mappings,
                                 envelope_protocols,
                                 envelope_template):

    envelope_content_keys = StreamingPolicyContentKeys(
        default_key=DefaultKey(label=envelope_default_key_label,
                               policy_name=envelope_default_key_policy_name),
        key_to_track_mappings=_parse_key_to_track_mappings_json(envelope_key_to_track_mappings))

    envelope_encryption = EnvelopeEncryption(enabled_protocols=_build_enabled_protocols_object(envelope_protocols),
                                             clear_tracks=_parse_clear_tracks_json(envelope_clear_tracks),
                                             content_keys=envelope_content_keys,
                                             custom_key_acquisition_url_template=envelope_template)

    return envelope_encryption


def get_streaming_policy(client, resource_group_name, account_name, streaming_policy_name):
    streaming_policy = client.get(resource_group_name, account_name, streaming_policy_name)
    if not streaming_policy:
        show_resource_not_found_message(resource_group_name, account_name, 'streamingPolicies', streaming_policy_name)

    return streaming_policy
