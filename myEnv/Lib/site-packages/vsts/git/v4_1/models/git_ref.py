# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitRef(Model):
    """GitRef.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param creator:
    :type creator: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param is_locked:
    :type is_locked: bool
    :param is_locked_by:
    :type is_locked_by: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param name:
    :type name: str
    :param object_id:
    :type object_id: str
    :param peeled_object_id:
    :type peeled_object_id: str
    :param statuses:
    :type statuses: list of :class:`GitStatus <git.v4_1.models.GitStatus>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'creator': {'key': 'creator', 'type': 'IdentityRef'},
        'is_locked': {'key': 'isLocked', 'type': 'bool'},
        'is_locked_by': {'key': 'isLockedBy', 'type': 'IdentityRef'},
        'name': {'key': 'name', 'type': 'str'},
        'object_id': {'key': 'objectId', 'type': 'str'},
        'peeled_object_id': {'key': 'peeledObjectId', 'type': 'str'},
        'statuses': {'key': 'statuses', 'type': '[GitStatus]'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, creator=None, is_locked=None, is_locked_by=None, name=None, object_id=None, peeled_object_id=None, statuses=None, url=None):
        super(GitRef, self).__init__()
        self._links = _links
        self.creator = creator
        self.is_locked = is_locked
        self.is_locked_by = is_locked_by
        self.name = name
        self.object_id = object_id
        self.peeled_object_id = peeled_object_id
        self.statuses = statuses
        self.url = url
