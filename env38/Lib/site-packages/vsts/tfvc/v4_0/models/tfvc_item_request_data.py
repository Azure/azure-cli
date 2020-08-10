# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcItemRequestData(Model):
    """TfvcItemRequestData.

    :param include_content_metadata: If true, include metadata about the file type
    :type include_content_metadata: bool
    :param include_links: Whether to include the _links field on the shallow references
    :type include_links: bool
    :param item_descriptors:
    :type item_descriptors: list of :class:`TfvcItemDescriptor <tfvc.v4_0.models.TfvcItemDescriptor>`
    """

    _attribute_map = {
        'include_content_metadata': {'key': 'includeContentMetadata', 'type': 'bool'},
        'include_links': {'key': 'includeLinks', 'type': 'bool'},
        'item_descriptors': {'key': 'itemDescriptors', 'type': '[TfvcItemDescriptor]'}
    }

    def __init__(self, include_content_metadata=None, include_links=None, item_descriptors=None):
        super(TfvcItemRequestData, self).__init__()
        self.include_content_metadata = include_content_metadata
        self.include_links = include_links
        self.item_descriptors = item_descriptors
