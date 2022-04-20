# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer

from azure.cli.command_modules.ams.operations.sp import list_role_definitions
from azure.cli.command_modules.ams._sdk_utils import (get_stand_alone_presets, get_cdn_providers,
                                                      get_default_streaming_policies, get_token_types,
                                                      get_rentalandlease_types, get_tokens,
                                                      get_allowed_languages_for_preset,
                                                      get_protocols, get_encoding_types,
                                                      get_allowed_resolutions, get_transcription_langauges,
                                                      get_analysis_modes, get_stretch_mode_types,
                                                      get_storage_authentication_allowed_values,
                                                      get_face_detector_modes, get_face_detector_blur_types,
                                                      get_encryption_key_types, get_default_action_allowed_values)

from azure.mgmt.media.models import EncoderNamedPreset


@Completer
def get_role_definition_name_completion_list(cmd):
    definitions = list_role_definitions(cmd)
    return [x.properties.role_name for x in list(definitions)]


def get_presets_definition_name_completion_list():
    encoder_name_presets_list = [e.value for e in EncoderNamedPreset]
    encoder_name_presets_list.extend(get_stand_alone_presets())
    return encoder_name_presets_list


def get_cdn_provider_completion_list():
    cdn_provider_list = get_cdn_providers()
    return cdn_provider_list


def get_default_streaming_policies_completion_list():
    default_streaming_policies = get_default_streaming_policies()
    return default_streaming_policies


def get_protocols_completion_list():
    protocols = get_protocols()
    return protocols


def get_token_type_completion_list():
    token_types = get_token_types()
    return token_types


def get_fairplay_rentalandlease_completion_list():
    rentalandlease_types = get_rentalandlease_types()
    return rentalandlease_types


def get_token_completion_list():
    tokens = get_tokens()
    return tokens


def get_allowed_languages_for_preset_completion_list():
    languages = get_allowed_languages_for_preset()
    return languages


def get_allowed_resolutions_completion_list():
    resolutions = get_allowed_resolutions()
    return resolutions


def get_mru_type_completion_list():
    return ['S1', 'S2', 'S3']


def get_encoding_types_list():
    encoding_types = get_encoding_types()
    return encoding_types


def get_allowed_transcription_languages():
    languages = get_transcription_langauges()
    return languages


def get_allowed_analysis_modes():
    modes = get_analysis_modes()
    return modes


def get_stretch_mode_types_list():
    modes = get_stretch_mode_types()
    return modes


def get_allowed_face_detector_modes():
    modes = get_face_detector_modes()
    return modes


def get_allowed_face_dectector_blur_types():
    types = get_face_detector_blur_types()
    return types


def get_allowed_encryption_key_types():
    types = get_encryption_key_types()
    return types


def get_storage_authentication_allowed_values_list():
    values = get_storage_authentication_allowed_values()
    return values


def get_default_action_allowed_values_list():
    values = get_default_action_allowed_values()
    return values
