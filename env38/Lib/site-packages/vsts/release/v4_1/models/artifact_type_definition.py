# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ArtifactTypeDefinition(Model):
    """ArtifactTypeDefinition.

    :param display_name:
    :type display_name: str
    :param endpoint_type_id:
    :type endpoint_type_id: str
    :param input_descriptors:
    :type input_descriptors: list of :class:`InputDescriptor <release.v4_1.models.InputDescriptor>`
    :param name:
    :type name: str
    :param unique_source_identifier:
    :type unique_source_identifier: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'endpoint_type_id': {'key': 'endpointTypeId', 'type': 'str'},
        'input_descriptors': {'key': 'inputDescriptors', 'type': '[InputDescriptor]'},
        'name': {'key': 'name', 'type': 'str'},
        'unique_source_identifier': {'key': 'uniqueSourceIdentifier', 'type': 'str'}
    }

    def __init__(self, display_name=None, endpoint_type_id=None, input_descriptors=None, name=None, unique_source_identifier=None):
        super(ArtifactTypeDefinition, self).__init__()
        self.display_name = display_name
        self.endpoint_type_id = endpoint_type_id
        self.input_descriptors = input_descriptors
        self.name = name
        self.unique_source_identifier = unique_source_identifier
