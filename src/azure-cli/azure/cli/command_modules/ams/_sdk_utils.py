# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
from azure.mgmt.media.models import (FaceRedactorMode, AudioAnalysisMode, BlurType, AccountEncryptionKeyType, DefaultAction)
models_module = importlib.import_module('azure.mgmt.media.models')


def get_sdk_model_class(class_name):
    return getattr(models_module, class_name)


def get_stand_alone_presets():
    return ['AudioAnalyzer', 'VideoAnalyzer', 'FaceDetector']


def get_cdn_providers():
    return ['StandardVerizon', 'PremiumVerizon', 'StandardAkamai']


def get_default_streaming_policies():
    return ['Predefined_DownloadOnly', 'Predefined_ClearStreamingOnly', 'Predefined_DownloadAndClearStreaming',
            'Predefined_ClearKey', 'Predefined_MultiDrmCencStreaming', 'Predefined_MultiDrmStreaming']


def get_token_types():
    return ['Jwt', 'Swt']


def get_rentalandlease_types():
    return ['Undefined', 'DualExpiry', 'PersistentUnlimited', 'PersistentLimited']


def get_tokens():
    return ['Symmetric', 'RSA', 'X509']


def get_protocols():
    return ['Download', 'Dash', 'HLS', 'SmoothStreaming']


def get_allowed_languages_for_preset():
    return ['en-US', 'en-GB', 'es-ES', 'es-MX', 'fr-FR', 'it-IT', 'ja-JP',
            'pt-BR', 'zh-CN', 'de-DE', 'ar-EG', 'ru-RU', 'hi-IN']


def get_allowed_resolutions():
    return ['StandardDefinition', 'SourceResolution']


def get_media_namespace():
    return 'Microsoft.Media'


def get_media_type():
    return 'mediaservices'


def get_encoding_types():
    return ['Premium1080p', 'None', 'Standard']


def get_transcription_langauges():
    return ['ca-ES', 'da-DK', 'de-DE', 'en-AU', 'en-CA', 'en-GB', 'en-IN', 'en-NZ', 'en-US', 'es-ES',
            'es-MX', 'fi-FI', 'fr-CA', 'fr-FR', 'it-IT', 'nl-NL', 'pt-BR', 'pt-PT', 'sv-SE']


def get_analysis_modes():
    return AudioAnalysisMode


def get_face_detector_modes():
    return FaceRedactorMode


def get_face_detector_blur_types():
    return BlurType


def get_stretch_mode_types():
    return ['None', 'AutoSize', 'AutoFit']


def get_encryption_key_types():
    return AccountEncryptionKeyType


def get_storage_authentication_allowed_values():
    return ['System', 'ManagedIdentity']


def get_default_action_allowed_values():
    return [DefaultAction.ALLOW, DefaultAction.DENY]
