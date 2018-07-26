# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib


models_module = importlib.import_module('azure.mgmt.media.models')


sdk_mes_formats_mapper = {'MP4Format':'Mp4Format'}


def map_format_type(format_type):
    return sdk_mes_formats_mapper.get(format_type, format_type)


sdk_mes_codecs_mapper = {'AACAudio':'AacAudio'}


def map_codec_type(codec_type):
    return sdk_mes_codecs_mapper.get(codec_type, codec_type)


def get_sdk_model_class(class_name):
    return getattr(models_module, class_name)


def get_stand_alone_presets():
    return ['AudioAnalyzer', 'VideoAnalyzer']