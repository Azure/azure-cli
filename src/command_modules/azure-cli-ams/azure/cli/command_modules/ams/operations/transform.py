# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_transform(client, account_name, resource_group_name,
                     transform_name, preset_names, description=None, tags=None):
    from azure.mediav3.models import Transform

    outputs = []

    for preset in preset_names:
        outputs.append(get_transform_output(preset))

    transform_parameters = Transform(outputs=outputs, location='westus2', description=description, tags=tags)

    return client.create_or_update(resource_group_name, account_name, transform_name, transform_parameters)


def add_transform_output(client, account_name, resource_group_name, transform_name, preset_names):
    transform = client.get(resource_group_name, account_name, transform_name)

    set_preset_names = set(preset_names)
    set_existent_preset_names = set(map(lambda x: x.preset.preset_name.value, transform.outputs))

    set_preset_names = set_preset_names.difference(set_existent_preset_names)

    for preset in set_preset_names:
        transform.outputs.append(get_transform_output(preset))

    return client.create_or_update(resource_group_name, account_name, transform_name, transform)


def remove_transform_output(client, account_name, resource_group_name, transform_name, preset_names):
    transform = client.get(resource_group_name, account_name, transform_name)

    set_preset_names = set(preset_names)
    set_existent_preset_names = set(map(lambda x: x.preset.preset_name.value, transform.outputs))

    set_existent_preset_names = set_existent_preset_names.difference(set_preset_names)

    transform_output_list = list(filter(lambda x: x.preset.preset_name.value in set_existent_preset_names,
                                        transform.outputs))
    transform.outputs = transform_output_list

    return client.create_or_update(resource_group_name, account_name, transform_name, transform)


def update_transform(client, account_name, resource_group_name,
                     transform_name, location=None, description=None, tags=None):
    transform = client.get(resource_group_name, account_name, transform_name)

    transform.location = transform.location if location is None else location
    transform.description = transform.description if description is None else description
    transform.tags = transform.tags if tags is None else tags

    return client.create_or_update(resource_group_name, account_name, transform_name, transform)


def transform_update_setter(client, resource_group_name,
                            account_name, transform_name, parameters):
    parameters.outputs = list(map(lambda x: get_transform_output(x) if isinstance(x, str) else x, parameters.outputs))
    return client.create_or_update(resource_group_name, account_name, transform_name, parameters)


def update_transform(instance, tags=None, description=None, preset_names=None):
    if not instance:
        raise CLIError('The transform resource was not found.')

    if description:
        instance.description = description

    if tags:
        instance.tags = tags

    if preset_names:
        instance.outputs = []
        for preset in preset_names:
            instance.outputs.append(get_transform_output(preset))

    return instance


def get_transform_output(preset):
    from azure.mediav3.models import (TransformOutput, BuiltInStandardEncoderPreset)
    transform_preset = BuiltInStandardEncoderPreset(preset_name=preset)
    transform_output = TransformOutput(preset=transform_preset)
    return transform_output
