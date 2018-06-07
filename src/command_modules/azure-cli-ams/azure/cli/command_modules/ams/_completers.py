# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer

from azure.cli.command_modules.ams.operations.sp import list_role_definitions

from azure.mgmt.media.models import (EncoderNamedPreset)


@Completer
def get_role_definition_name_completion_list(cmd):
    definitions = list_role_definitions(cmd)
    return [x.properties.role_name for x in list(definitions)]


def get_presets_definition_name_completion_list():
    encoder_name_presets_list = [e.value for e in EncoderNamedPreset]
    encoder_name_presets_list.extend(get_stand_alone_presets())
    return encoder_name_presets_list


def get_stand_alone_presets():
    return ['AudioAnalyzer', 'VideoAnalyzer']


def is_audio_analyzer(preset_name):
    return preset_name == 'AudioAnalyzer'
