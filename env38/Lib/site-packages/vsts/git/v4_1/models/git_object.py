# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitObject(Model):
    """GitObject.

    :param object_id: Object Id (Sha1Id).
    :type object_id: str
    :param object_type: Type of object (Commit, Tree, Blob, Tag)
    :type object_type: object
    """

    _attribute_map = {
        'object_id': {'key': 'objectId', 'type': 'str'},
        'object_type': {'key': 'objectType', 'type': 'object'}
    }

    def __init__(self, object_id=None, object_type=None):
        super(GitObject, self).__init__()
        self.object_id = object_id
        self.object_type = object_type
