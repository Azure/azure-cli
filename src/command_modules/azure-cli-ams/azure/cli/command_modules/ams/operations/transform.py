# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib, json, re, isodate
from datetime import datetime, timedelta

from knack.util import CLIError

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
                standard_encoder_preset = StandardEncoderPreset(codecs=build_codecs_for_preset(custom_preset_json['Codecs']))
                outputs.append(TransformOutput(preset=standard_encoder_preset))
        except (OSError, IOError) as e:
            raise CLIError("Can't find a valid custom preset JSON definition in '{}'".format(custom_preset_path))

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


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


models_module = importlib.import_module('azure.mgmt.media.models')

def build_codecs_for_preset(codecs):
    codec_instance_list = []
    for codec in codecs:
        codec_instance = getattr(models_module, codec['Type'])()
        layers = []
        for key, value in codec.items():
            if isinstance(value, list) and 'Layers' in key:
                layer_type = key[:-1]
                layer_instance = getattr(models_module, layer_type)()
                for layer_group in value:
                    for layer_prop_key, layer_prop_value in layer_group.items():
                        parse_custom_preset_value(layer_prop_key, layer_prop_value, layer_instance)
                    layers.append(layer_instance)
            else:
                parse_custom_preset_value(key, value, codec_instance)
        if len(layers) > 0:
            codec_instance.layers = layers

        codec_instance_list.append(codec_instance)
    return codec_instance_list


def parse_custom_preset_value(key, value, instance):
    if hasattr(instance, camel_to_snake(key)):
        try:
            datetime_duration = datetime.strptime(value,'%H:%M:%S')
            iso_duration_format_value = isodate.duration_isoformat(timedelta(hours=datetime_duration.hour,
                                                                             minutes=datetime_duration.minute,
                                                                             seconds=datetime_duration.second))
            setattr(instance, camel_to_snake(key), iso_duration_format_value)
        except:
            setattr(instance, camel_to_snake(key), value)