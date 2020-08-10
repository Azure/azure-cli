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

    :param _links: A collection of REST reference links.
    :type _links: :class:`ReferenceLinks <tfvc.v4_1.models.ReferenceLinks>`
    :param author: Alias or display name of user
    :type author: :class:`IdentityRef <tfvc.v4_1.models.IdentityRef>`
    :param changeset_id: Id of the changeset.
    :type changeset_id: int
    :param checked_in_by: Alias or display name of user
    :type checked_in_by: :class:`IdentityRef <tfvc.v4_1.models.IdentityRef>`
    :param comment: Comment for the changeset.
    :type comment: str
    :param comment_truncated: Was the Comment result truncated?
    :type comment_truncated: bool
    :param created_date: Creation date of the changeset.
    :type created_date: datetime
    :param url: URL to retrieve the item.
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
