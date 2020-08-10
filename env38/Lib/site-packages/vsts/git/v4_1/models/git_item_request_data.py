# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitItemRequestData(Model):
    """GitItemRequestData.

    :param include_content_metadata: Whether to include metadata for all items
    :type include_content_metadata: bool
    :param include_links: Whether to include the _links field on the shallow references
    :type include_links: bool
    :param item_descriptors: Collection of items to fetch, including path, version, and recursion level
    :type item_descriptors: list of :class:`GitItemDescriptor <git.v4_1.models.GitItemDescriptor>`
    :param latest_processed_change: Whether to include shallow ref to commit that last changed each item
    :type latest_processed_change: bool
    """

    _attribute_map = {
        'include_content_metadata': {'key': 'includeContentMetadata', 'type': 'bool'},
        'include_links': {'key': 'includeLinks', 'type': 'bool'},
        'item_descriptors': {'key': 'itemDescriptors', 'type': '[GitItemDescriptor]'},
        'latest_processed_change': {'key': 'latestProcessedChange', 'type': 'bool'}
    }

    def __init__(self, include_content_metadata=None, include_links=None, item_descriptors=None, latest_processed_change=None):
        super(GitItemRequestData, self).__init__()
        self.include_content_metadata = include_content_metadata
        self.include_links = include_links
        self.item_descriptors = item_descriptors
        self.latest_processed_change = latest_processed_change
