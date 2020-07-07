# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionFilterResult(Model):
    """ExtensionFilterResult.

    :param extensions: This is the set of appplications that matched the query filter supplied.
    :type extensions: list of :class:`PublishedExtension <gallery.v4_1.models.PublishedExtension>`
    :param paging_token: The PagingToken is returned from a request when more records exist that match the result than were requested or could be returned. A follow-up query with this paging token can be used to retrieve more results.
    :type paging_token: str
    :param result_metadata: This is the additional optional metadata for the given result. E.g. Total count of results which is useful in case of paged results
    :type result_metadata: list of :class:`ExtensionFilterResultMetadata <gallery.v4_1.models.ExtensionFilterResultMetadata>`
    """

    _attribute_map = {
        'extensions': {'key': 'extensions', 'type': '[PublishedExtension]'},
        'paging_token': {'key': 'pagingToken', 'type': 'str'},
        'result_metadata': {'key': 'resultMetadata', 'type': '[ExtensionFilterResultMetadata]'}
    }

    def __init__(self, extensions=None, paging_token=None, result_metadata=None):
        super(ExtensionFilterResult, self).__init__()
        self.extensions = extensions
        self.paging_token = paging_token
        self.result_metadata = result_metadata
