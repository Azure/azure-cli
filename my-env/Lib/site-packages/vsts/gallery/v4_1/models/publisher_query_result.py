# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PublisherQueryResult(Model):
    """PublisherQueryResult.

    :param results: For each filter supplied in the query, a filter result will be returned in the query result.
    :type results: list of :class:`PublisherFilterResult <gallery.v4_1.models.PublisherFilterResult>`
    """

    _attribute_map = {
        'results': {'key': 'results', 'type': '[PublisherFilterResult]'}
    }

    def __init__(self, results=None):
        super(PublisherQueryResult, self).__init__()
        self.results = results
