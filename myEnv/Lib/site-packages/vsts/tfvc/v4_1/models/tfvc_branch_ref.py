# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .tfvc_shallow_branch_ref import TfvcShallowBranchRef


class TfvcBranchRef(TfvcShallowBranchRef):
    """TfvcBranchRef.

    :param path: Path for the branch.
    :type path: str
    :param _links: A collection of REST reference links.
    :type _links: :class:`ReferenceLinks <tfvc.v4_1.models.ReferenceLinks>`
    :param created_date: Creation date of the branch.
    :type created_date: datetime
    :param description: Description of the branch.
    :type description: str
    :param is_deleted: Is the branch deleted?
    :type is_deleted: bool
    :param owner: Alias or display name of user
    :type owner: :class:`IdentityRef <tfvc.v4_1.models.IdentityRef>`
    :param url: URL to retrieve the item.
    :type url: str
    """

    _attribute_map = {
        'path': {'key': 'path', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, path=None, _links=None, created_date=None, description=None, is_deleted=None, owner=None, url=None):
        super(TfvcBranchRef, self).__init__(path=path)
        self._links = _links
        self.created_date = created_date
        self.description = description
        self.is_deleted = is_deleted
        self.owner = owner
        self.url = url
