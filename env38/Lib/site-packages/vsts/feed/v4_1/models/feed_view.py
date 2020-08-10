# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FeedView(Model):
    """FeedView.

    :param _links:
    :type _links: :class:`ReferenceLinks <packaging.v4_1.models.ReferenceLinks>`
    :param id:
    :type id: str
    :param name:
    :type name: str
    :param type:
    :type type: object
    :param url:
    :type url: str
    :param visibility:
    :type visibility: object
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'},
        'visibility': {'key': 'visibility', 'type': 'object'}
    }

    def __init__(self, _links=None, id=None, name=None, type=None, url=None, visibility=None):
        super(FeedView, self).__init__()
        self._links = _links
        self.id = id
        self.name = name
        self.type = type
        self.url = url
        self.visibility = visibility
