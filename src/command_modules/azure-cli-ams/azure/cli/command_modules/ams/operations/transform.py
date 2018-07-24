# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# Licensed under the MIT License.  See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------------------------

import json

from knack.util import CLIError

from azure.cli.command_modules.ams._sdk_utils import (map_format_type, map_codec_type, get_sdk_model_class)
from azure.cli.command_modules.ams._utils import (parse_iso_duration, camel_to_snake)

# pylint: disable=line-too-long

def create_transform(cmd, client, account_name, resource_group_name,
                     transform_name, preset_names=None, description=None,
                     custom_preset_path=None):
    outputs = []

    if custom_preset_path is None and preset_names is None:
        raise CLIError("Missing required arguments.\nEither --preset-names "
                           "or --custom-preset must be specified.")

    if preset_names:
        for preset in preset_names:
            outputs.append(get_transform_output(preset))

    if custom_preset_path:
        try:
            with open(custom_preset_path) as custom_preset_json_stream:
                custom_preset_json = json.load(custom_preset_json_stream)
                from azure.mgmt.media.models import (StandardEncoderPreset, TransformOutput)
                standard_encoder_preset = StandardEncoderPreset(codecs=map_codecs(custom_preset_json['Codecs']),
                                                                filters=map_filters(custom_preset_json),
                                                                formats=map_formats(custom_preset_json['Outputs']))
                outputs.append(TransformOutput(preset=standard_encoder_preset))
        except:
            raise CLIError("Couldn't find a valid custom preset JSON definition in '{}'. Check the schema is correct."
                           .format(custom_preset_path))

    return client.create_or_update(resource_group_name, account_name, transform_name, outputs, description)


def add_transform_output(client, account_name, resource_group_name, transform_name, preset_names):
    transform = client.get(resource_group_name, account_name, transform_name)

    set_preset_names = set(preset_names)
    set_existent_preset_names = set(map(lambda x: x.preset.preset_name.value, transform.outputs))

    set_preset_names = set_preset_names.difference(set_existent_preset_names)

    for preset in set_preset_names:
        transform.outputs.append(get_transform_output(preset))

    return client.create_or_update(resource_group_name, account_name, transform_name, transform.outputs)


def remove_transform_output(client, account_name, resource_group_name, transform_name, preset_names):
    transform = client.get(resource_group_name, account_name, transform_name)

    set_preset_names = set(preset_names)
    set_existent_preset_names = set(map(lambda x: x.preset.preset_name.value, transform.outputs))

    set_existent_preset_names = set_existent_preset_names.difference(set_preset_names)

    transform_output_list = list(filter(lambda x: x.preset.preset_name.value in set_existent_preset_names,
                                        transform.outputs))

    return client.create_or_update(resource_group_name, account_name, transform_name, transform_output_list)


def transform_update_setter(client, resource_group_name,
                            account_name, transform_name, parameters):
    parameters.outputs = list(map(lambda x: get_transform_output(x) if isinstance(x, str) else x, parameters.outputs))
    return client.create_or_update(resource_group_name, account_name, transform_name,
                                   parameters.outputs, parameters.description)


def update_transform(instance, description=None, preset_names=None):
    if not instance:
        raise CLIError('The transform resource was not found.')

    if description:
        instance.description = description

    if preset_names:
        instance.outputs = []
        for preset in preset_names:
            instance.outputs.append(get_transform_output(preset))

    return instance


def get_transform_output(preset):
    from azure.mgmt.media.models import (TransformOutput, BuiltInStandardEncoderPreset, VideoAnalyzerPreset, AudioAnalyzerPreset)
    from azure.cli.command_modules.ams._completers import (get_stand_alone_presets, is_audio_analyzer)

    if preset in get_stand_alone_presets():
        if is_audio_analyzer(preset_name=preset):
            transform_preset = AudioAnalyzerPreset()
        else:
            transform_preset = VideoAnalyzerPreset()
    else:
        transform_preset = BuiltInStandardEncoderPreset(preset_name=preset)

    transform_output = TransformOutput(preset=transform_preset)
    return transform_output


def map_codecs(codecs):
    codec_instance_list = []
    for codec in codecs:
        try:
            codec_instance = get_sdk_model_class(map_codec_type(codec['Type']))()
            layers = []
            for key, value in codec.items():
                if isinstance(value, list) and 'Layers' in key:
                    layer_type = key[:-1]
                    layer_instance = get_sdk_model_class(layer_type)()
                    for layer_group in value:
                        for layer_prop_key, layer_prop_value in layer_group.items():
                            parse_custom_preset_value(layer_prop_key, layer_prop_value, layer_instance)
                        layers.append(layer_instance)
                else:
                    parse_custom_preset_value(key, value, codec_instance)
        except Exception as ex:
            raise CLIError("Invalid or unsupported codec type in your custom preset JSON file.")

        if len(layers) > 0:
            codec_instance.layers = layers

        codec_instance_list.append(codec_instance)
    return codec_instance_list


def map_filters(custom_preset_json):
    filters_instance = None

    sources = custom_preset_json.get('Sources')
    if sources:
        for source in sources:
            filters = source.get('Filters')
            if filters:
                from azure.mgmt.media.models import Filters
                filters_instance = Filters()
            
                overlays = []

                video_overlay = filters.get('VideoOverlay')
                if video_overlay:
                    from azure.mgmt.media.models import VideoOverlay
                    video_overlay_instance = VideoOverlay()

                    position = video_overlay.get('Position')
                    video_overlay_instance.position = map_position(position)

                    video_overlay_instance.audio_gain_level = video_overlay.get('AudioGainLevel')
                    video_overlay_instance.input_label = video_overlay.get('Source')

                    video_overlay_instance.fade_in_duration = map_fade_in_out_duration(video_overlay.get('FadeInDuration'))
                    video_overlay_instance.fade_out_duration = map_fade_in_out_duration(video_overlay.get('FadeOutDuration'))

                    overlays.append(video_overlay_instance)

                    # TODO: start, end, opacity, crop_rectangle parameters
            
                audio_overlay = filters.get('AudioOverlay')
                if audio_overlay:
                    from azure.mgmt.media.models import AudioOverlay
                    audio_overlay_instance = AudioOverlay()

                    position = audio_overlay.get('Position')
                    audio_overlay_instance.position = map_position(position)

                    audio_overlay_instance.audio_gain_level = audio_overlay.get('AudioGainLevel')
                    audio_overlay_instance.input_label = audio_overlay.get('Source')

                    audio_overlay_instance.fade_in_duration = map_fade_in_out_duration(audio_overlay.get('FadeInDuration'))
                    audio_overlay_instance.fade_out_duration = map_fade_in_out_duration(audio_overlay.get('FadeOutDuration'))

                    overlays.append(audio_overlay_instance)

                    # TODO: start, end parameters
            
                filters_instance.deinterlace = filters.get('Deinterlace')
            
                rotation = filters.get('Rotation')
                if rotation:
                    filters_instance.rotation = 'Rotate{}'.format(rotation)
            
                # TODO: crop parameter

                filters_instance.overlays = overlays


    return filters_instance


def map_formats(outputs):
    formats = []
    for output in outputs:
        try:
            format_instance = get_sdk_model_class(map_format_type(output['Format']['Type']))()
            format_instance.filename_pattern = output['FileName']
        except:
            raise CLIError("Invalid or unsupported format type in your custom preset JSON file.")
        formats.append(format_instance)
    return formats


def parse_custom_preset_value(key, value, instance):
    if hasattr(instance, camel_to_snake(key)):
        try:
            iso_duration = parse_iso_duration(value)
            setattr(instance, camel_to_snake(key), iso_duration)
        except:
            setattr(instance, camel_to_snake(key), value)


def map_position(position):
    rectangle = None
    if position:
        from azure.mgmt.media.models import Rectangle
        rectangle = Rectangle(left=position.get('X'), top=position.get('Y'),
                              width=position.get('Width'), height=position.get('Height'))
    return rectangle


def map_fade_in_out_duration(obj):
    iso_duration = None
    if obj:
        iso_duration = parse_iso_duration(obj.get('Duration'))
    return iso_duration
