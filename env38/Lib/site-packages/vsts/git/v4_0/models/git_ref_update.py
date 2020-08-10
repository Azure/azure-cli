# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitRefUpdate(Model):
    """GitRefUpdate.

    :param is_locked:
    :type is_locked: bool
    :param name:
    :type name: str
    :param new_object_id:
    :type new_object_id: str
    :param old_object_id:
    :type old_object_id: str
    :param repository_id:
    :type repository_id: str
    """

    _attribute_map = {
        'is_locked': {'key': 'isLocked', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'new_object_id': {'key': 'newObjectId', 'type': 'str'},
        'old_object_id': {'key': 'oldObjectId', 'type': 'str'},
        'repository_id': {'key': 'repositoryId', 'type': 'str'}
    }

    def __init__(self, is_locked=None, name=None, new_object_id=None, old_object_id=None, repository_id=None):
        super(GitRefUpdate, self).__init__()
        self.is_locked = is_locked
        self.name = name
        self.new_object_id = new_object_id
        self.old_object_id = old_object_id
        self.repository_id = repository_id
