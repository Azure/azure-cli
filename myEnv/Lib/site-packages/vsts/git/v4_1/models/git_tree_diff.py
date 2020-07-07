# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitTreeDiff(Model):
    """GitTreeDiff.

    :param base_tree_id: ObjectId of the base tree of this diff.
    :type base_tree_id: str
    :param diff_entries: List of tree entries that differ between the base and target tree.  Renames and object type changes are returned as a delete for the old object and add for the new object.  If a continuation token is returned in the response header, some tree entries are yet to be processed and may yeild more diff entries. If the continuation token is not returned all the diff entries have been included in this response.
    :type diff_entries: list of :class:`GitTreeDiffEntry <git.v4_1.models.GitTreeDiffEntry>`
    :param target_tree_id: ObjectId of the target tree of this diff.
    :type target_tree_id: str
    :param url: REST Url to this resource.
    :type url: str
    """

    _attribute_map = {
        'base_tree_id': {'key': 'baseTreeId', 'type': 'str'},
        'diff_entries': {'key': 'diffEntries', 'type': '[GitTreeDiffEntry]'},
        'target_tree_id': {'key': 'targetTreeId', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, base_tree_id=None, diff_entries=None, target_tree_id=None, url=None):
        super(GitTreeDiff, self).__init__()
        self.base_tree_id = base_tree_id
        self.diff_entries = diff_entries
        self.target_tree_id = target_tree_id
        self.url = url
