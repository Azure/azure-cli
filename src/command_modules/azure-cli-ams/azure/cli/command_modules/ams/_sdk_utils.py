# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib

models_module = importlib.import_module('azure.mgmt.media.models')
sdk_mes_codecs_mapper = {'AACAudio': 'AacAudio'}
sdk_mes_formats_mapper = {'MP4Format': 'Mp4Format'}


def map_format_type(format_type):
    return sdk_mes_formats_mapper.get(format_type, format_type)


def map_codec_type(codec_type):
    return sdk_mes_codecs_mapper.get(codec_type, codec_type)


def get_sdk_model_class(class_name):
    return getattr(models_module, class_name)


def get_stand_alone_presets():
    return ['AudioAnalyzer', 'VideoAnalyzer']


def get_cdn_providers():
    return ['StandardVerizon', 'PremiumVerizon', 'StandardAkamai']


def get_default_streaming_policies():
    return ['Predefined_DownloadOnly', 'Predefined_ClearStreamingOnly', 'Predefined_DownloadAndClearStreaming',
            'Predefined_ClearKey', 'Predefined_SecureStreaming', 'Predefined_SecureStreamingWithFairPlay']


def get_token_types():
    return ['Jwt', 'Swt']


def get_rentalandlease_types():
    return ['Undefined', 'PersistentUnlimited', 'PersistentLimited']


def get_tokens():
    return ['Symmetric', 'RSA', 'X509']
