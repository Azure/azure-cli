# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcChangesetRef(Model):
    """TfvcChangesetRef.

    :param _links:
    :type _links: :class:`ReferenceLinks <tfvc.v4_0.models.ReferenceLinks>`
    :param author:
    :type author: :class:`IdentityRef <tfvc.v4_0.models.IdentityRef>`
    :param changeset_id:
    :type changeset_id: int
    :param checked_in_by:
    :type checked_in_by: :class:`IdentityRef <tfvc.v4_0.models.IdentityRef>`
    :param comment:
    :type comment: str
    :param comment_truncated:
    :type comment_truncated: bool
    :param created_date:
    :type created_date: datetime
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'author': {'key': 'author', 'type': 'IdentityRef'},
        'changeset_id': {'key': 'changesetId', 'type': 'int'},
        'checked_in_by': {'key': 'checkedInBy', 'type': 'IdentityRef'},
        'comment': {'key': 'comment', 'type': 'str'},
        'comment_truncated': {'key': 'commentTruncated', 'type': 'bool'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, author=None, changeset_id=None, checked_in_by=None, comment=None, comment_truncated=None, created_date=None, url=None):
        super(TfvcChangesetRef, self).__init__()
        self._links = _links
        self.author = author
        self.changeset_id = changeset_id
        self.checked_in_by = checked_in_by
        self.comment = comment
        self.comment_truncated = comment_truncated
        self.created_date = created_date
        self.url = url
