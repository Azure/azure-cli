# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitBlobRef(Model):
    """GitBlobRef.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_0.models.ReferenceLinks>`
    :param object_id: SHA1 hash of git object
    :type object_id: str
    :param size: Size of blob content (in bytes)
    :type size: long
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'object_id': {'key': 'objectId', 'type': 'str'},
        'size': {'key': 'size', 'type': 'long'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, object_id=None, size=None, url=None):
        super(GitBlobRef, self).__init__()
        self._links = _links
        self.object_id = object_id
        self.size = size
        self.url = url
