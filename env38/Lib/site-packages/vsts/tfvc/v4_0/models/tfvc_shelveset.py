# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .tfvc_shelveset_ref import TfvcShelvesetRef


class TfvcShelveset(TfvcShelvesetRef):
    """TfvcShelveset.

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
    :param changes:
    :type changes: list of :class:`TfvcChange <tfvc.v4_0.models.TfvcChange>`
    :param notes:
    :type notes: list of :class:`CheckinNote <tfvc.v4_0.models.CheckinNote>`
    :param policy_override:
    :type policy_override: :class:`TfvcPolicyOverrideInfo <tfvc.v4_0.models.TfvcPolicyOverrideInfo>`
    :param work_items:
    :type work_items: list of :class:`AssociatedWorkItem <tfvc.v4_0.models.AssociatedWorkItem>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'comment': {'key': 'comment', 'type': 'str'},
        'comment_truncated': {'key': 'commentTruncated', 'type': 'bool'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'url': {'key': 'url', 'type': 'str'},
        'changes': {'key': 'changes', 'type': '[TfvcChange]'},
        'notes': {'key': 'notes', 'type': '[CheckinNote]'},
        'policy_override': {'key': 'policyOverride', 'type': 'TfvcPolicyOverrideInfo'},
        'work_items': {'key': 'workItems', 'type': '[AssociatedWorkItem]'}
    }

    def __init__(self, _links=None, comment=None, comment_truncated=None, created_date=None, id=None, name=None, owner=None, url=None, changes=None, notes=None, policy_override=None, work_items=None):
        super(TfvcShelveset, self).__init__(_links=_links, comment=comment, comment_truncated=comment_truncated, created_date=created_date, id=id, name=name, owner=owner, url=url)
        self.changes = changes
        self.notes = notes
        self.policy_override = policy_override
        self.work_items = work_items
