# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcShelvesetRef(Model):
    """TfvcShelvesetRef.

    :param _links:
    :type _links: :class:`ReferenceLinks <tfvc.v4_0.models.ReferenceLinks>`
    :param comment:
    :type comment: str
    :param comment_truncated:
    :type comment_truncated: bool
    :param created_date:
    :type created_date: datetime
    :param id:
    :type id: str
    :param name:
    :type name: str
    :param owner:
    :type owner: :class:`IdentityRef <tfvc.v4_0.models.IdentityRef>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'comment': {'key': 'comment', 'type': 'str'},
        'comment_truncated': {'key': 'commentTruncated', 'type': 'bool'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, comment=None, comment_truncated=None, created_date=None, id=None, name=None, owner=None, url=None):
        super(TfvcShelvesetRef, self).__init__()
        self._links = _links
        self.comment = comment
        self.comment_truncated = comment_truncated
        self.created_date = created_date
        self.id = id
        self.name = name
        self.owner = owner
        self.url = url
