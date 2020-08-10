# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionFilterResultMetadata(Model):
    """ExtensionFilterResultMetadata.

    :param metadata_items: The metadata items for the category
    :type metadata_items: list of :class:`MetadataItem <gallery.v4_0.models.MetadataItem>`
    :param metadata_type: Defines the category of metadata items
    :type metadata_type: str
    """

    _attribute_map = {
        'metadata_items': {'key': 'metadataItems', 'type': '[MetadataItem]'},
        'metadata_type': {'key': 'metadataType', 'type': 'str'}
    }

    def __init__(self, metadata_items=None, metadata_type=None):
        super(ExtensionFilterResultMetadata, self).__init__()
        self.metadata_items = metadata_items
        self.metadata_type = metadata_type
