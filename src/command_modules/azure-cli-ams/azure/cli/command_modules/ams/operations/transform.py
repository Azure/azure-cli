# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_transform(client, account_name, resource_group_name, transform_name, preset_name, location=None):
    from azure.mediav3.models import (Transform, TransformOutput, BuiltInStandardEncoderPreset)

    transform_preset = BuiltInStandardEncoderPreset(preset_name=preset_name)
    transform_output = TransformOutput(preset=transform_preset)
    transform_parameters = Transform(outputs=[transform_output], location=location)

    return client.create_or_update(resource_group_name, account_name, transform_name, transform_parameters)
