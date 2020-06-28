# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitTreeRef(Model):
    """GitTreeRef.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param object_id: SHA1 hash of git object
    :type object_id: str
    :param size: Sum of sizes of all children
    :type size: long
    :param tree_entries: Blobs and trees under this tree
    :type tree_entries: list of :class:`GitTreeEntryRef <git.v4_1.models.GitTreeEntryRef>`
    :param url: Url to tree
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'object_id': {'key': 'objectId', 'type': 'str'},
        'size': {'key': 'size', 'type': 'long'},
        'tree_entries': {'key': 'treeEntries', 'type': '[GitTreeEntryRef]'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, object_id=None, size=None, tree_entries=None, url=None):
        super(GitTreeRef, self).__init__()
        self._links = _links
        self.object_id = object_id
        self.size = size
        self.tree_entries = tree_entries
        self.url = url
