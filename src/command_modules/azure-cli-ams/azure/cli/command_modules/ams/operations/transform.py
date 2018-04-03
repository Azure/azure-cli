# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_transform(client, account_name, resource_group_name, transform_name, preset_name, description=None, tags=None):
    from azure.mediav3.models import (Transform, TransformOutput, BuiltInStandardEncoderPreset)

    transform_preset = BuiltInStandardEncoderPreset(preset_name=preset_name)
    transform_output = TransformOutput(preset=transform_preset)
    transform_parameters = Transform(outputs=[transform_output], location='westus2', description=description, tags=tags)

    return client.create_or_update(resource_group_name, account_name, transform_name, transform_parameters)


def add_transform_output(cmd, client, account_name, resource_group_name, transform_name, preset_name):
    from azure.mediav3.models import (TransformOutput, BuiltInStandardEncoderPreset)

    transform = client.get(resource_group_name, account_name, transform_name)

    if not list(filter(lambda x: x.preset.preset_name.value == preset_name, transform.outputs)):
        transform_preset = BuiltInStandardEncoderPreset(preset_name=preset_name)
        transform_output = TransformOutput(preset=transform_preset)
        transform.outputs.append(transform_output)

    return client.create_or_update(resource_group_name, account_name, transform_name, transform)


def remove_transform_output(client, account_name, resource_group_name, transform_name, preset_name):
    transform = client.get(resource_group_name, account_name, transform_name)

    transform_output_list = list(filter(lambda x: x.preset.preset_name.value != preset_name, transform.outputs))
    transform.outputs = transform_output_list

    return client.create_or_update(resource_group_name, account_name, transform_name, transform)


def update_transform(client, account_name, resource_group_name, transform_name, location=None, description=None, tags=None):
    transform = client.get(resource_group_name, account_name, transform_name)

    transform.location = transform.location if location is None else location
    transform.description = transform.description if description is None else description
    transform.tags = transform.tags if tags is None else tags

    return client.create_or_update(resource_group_name, account_name, transform_name, transform)
