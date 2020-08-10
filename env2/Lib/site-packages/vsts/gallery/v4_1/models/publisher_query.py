# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PublisherQuery(Model):
    """PublisherQuery.

    :param filters: Each filter is a unique query and will have matching set of publishers returned from the request. Each result will have the same index in the resulting array that the filter had in the incoming query.
    :type filters: list of :class:`QueryFilter <gallery.v4_1.models.QueryFilter>`
    :param flags: The Flags are used to deterine which set of information the caller would like returned for the matched publishers.
    :type flags: object
    """

    _attribute_map = {
        'filters': {'key': 'filters', 'type': '[QueryFilter]'},
        'flags': {'key': 'flags', 'type': 'object'}
    }

    def __init__(self, filters=None, flags=None):
        super(PublisherQuery, self).__init__()
        self.filters = filters
        self.flags = flags
