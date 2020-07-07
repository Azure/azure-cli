# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PublisherFilterResult(Model):
    """PublisherFilterResult.

    :param publishers: This is the set of appplications that matched the query filter supplied.
    :type publishers: list of :class:`Publisher <gallery.v4_1.models.Publisher>`
    """

    _attribute_map = {
        'publishers': {'key': 'publishers', 'type': '[Publisher]'}
    }

    def __init__(self, publishers=None):
        super(PublisherFilterResult, self).__init__()
        self.publishers = publishers
