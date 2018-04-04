# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_transform(client, account_name, resource_group_name,
                     transform_name, preset_names, description=None, tags=None):
    from azure.mediav3.models import (Transform, TransformOutput, BuiltInStandardEncoderPreset)

    outputs = []

    for preset in preset_names:
        transform_preset = BuiltInStandardEncoderPreset(preset_name=preset)
        transform_output = TransformOutput(preset=transform_preset)
        outputs.append(transform_output)

    transform_parameters = Transform(outputs=outputs, location='westus2', description=description, tags=tags)

    return client.create_or_update(resource_group_name, account_name, transform_name, transform_parameters)


def add_transform_output(client, account_name, resource_group_name, transform_name, preset_names):
    from azure.mediav3.models import (TransformOutput, BuiltInStandardEncoderPreset)

    transform = client.get(resource_group_name, account_name, transform_name)

    set_preset_names = set(preset_names)
    set_existent_preset_names = set(map(lambda x: x.preset.preset_name.value, transform.outputs))

    set_preset_names = set_preset_names.difference(set_existent_preset_names)

    for preset in set_preset_names:
        transform_preset = BuiltInStandardEncoderPreset(preset_name=preset)
        transform_output = TransformOutput(preset=transform_preset)
        transform.outputs.append(transform_output)

    return client.create_or_update(resource_group_name, account_name, transform_name, transform)


def remove_transform_output(client, account_name, resource_group_name, transform_name, preset_names):
    transform = client.get(resource_group_name, account_name, transform_name)

    set_preset_names = set(preset_names)
    set_existent_preset_names = set(map(lambda x: x.preset.preset_name.value, transform.outputs))

    set_existent_preset_names = set_existent_preset_names.difference(set_preset_names)

    transform_output_list = list(filter(lambda x: x.preset.preset_name.value in set_existent_preset_names, transform.outputs))
    transform.outputs = transform_output_list

    return client.create_or_update(resource_group_name, account_name, transform_name, transform)


def update_transform(client, account_name, resource_group_name,
                     transform_name, location=None, description=None, tags=None):
    transform = client.get(resource_group_name, account_name, transform_name)

    transform.location = transform.location if location is None else location
    transform.description = transform.description if description is None else description
    transform.tags = transform.tags if tags is None else tags

    return client.create_or_update(resource_group_name, account_name, transform_name, transform)
