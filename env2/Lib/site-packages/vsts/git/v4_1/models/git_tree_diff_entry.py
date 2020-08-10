# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitTreeDiffEntry(Model):
    """GitTreeDiffEntry.

    :param base_object_id: SHA1 hash of the object in the base tree, if it exists. Will be null in case of adds.
    :type base_object_id: str
    :param change_type: Type of change that affected this entry.
    :type change_type: object
    :param object_type: Object type of the tree entry. Blob, Tree or Commit("submodule")
    :type object_type: object
    :param path: Relative path in base and target trees.
    :type path: str
    :param target_object_id: SHA1 hash of the object in the target tree, if it exists. Will be null in case of deletes.
    :type target_object_id: str
    """

    _attribute_map = {
        'base_object_id': {'key': 'baseObjectId', 'type': 'str'},
        'change_type': {'key': 'changeType', 'type': 'object'},
        'object_type': {'key': 'objectType', 'type': 'object'},
        'path': {'key': 'path', 'type': 'str'},
        'target_object_id': {'key': 'targetObjectId', 'type': 'str'}
    }

    def __init__(self, base_object_id=None, change_type=None, object_type=None, path=None, target_object_id=None):
        super(GitTreeDiffEntry, self).__init__()
        self.base_object_id = base_object_id
        self.change_type = change_type
        self.object_type = object_type
        self.path = path
        self.target_object_id = target_object_id
