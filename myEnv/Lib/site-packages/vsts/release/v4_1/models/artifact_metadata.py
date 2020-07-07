# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ArtifactMetadata(Model):
    """ArtifactMetadata.

    :param alias: Sets alias of artifact.
    :type alias: str
    :param instance_reference: Sets instance reference of artifact. e.g. for build artifact it is build number.
    :type instance_reference: :class:`BuildVersion <release.v4_1.models.BuildVersion>`
    """

    _attribute_map = {
        'alias': {'key': 'alias', 'type': 'str'},
        'instance_reference': {'key': 'instanceReference', 'type': 'BuildVersion'}
    }

    def __init__(self, alias=None, instance_reference=None):
        super(ArtifactMetadata, self).__init__()
        self.alias = alias
        self.instance_reference = instance_reference
