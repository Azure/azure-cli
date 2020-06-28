# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .tfvc_changeset_ref import TfvcChangesetRef


class TfvcChangeset(TfvcChangesetRef):
    """TfvcChangeset.

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
    :param account_id: Account Id of the changeset.
    :type account_id: str
    :param changes: List of associated changes.
    :type changes: list of :class:`TfvcChange <tfvc.v4_1.models.TfvcChange>`
    :param checkin_notes: Checkin Notes for the changeset.
    :type checkin_notes: list of :class:`CheckinNote <tfvc.v4_1.models.CheckinNote>`
    :param collection_id: Collection Id of the changeset.
    :type collection_id: str
    :param has_more_changes: Are more changes available.
    :type has_more_changes: bool
    :param policy_override: Policy Override for the changeset.
    :type policy_override: :class:`TfvcPolicyOverrideInfo <tfvc.v4_1.models.TfvcPolicyOverrideInfo>`
    :param team_project_ids: Team Project Ids for the changeset.
    :type team_project_ids: list of str
    :param work_items: List of work items associated with the changeset.
    :type work_items: list of :class:`AssociatedWorkItem <tfvc.v4_1.models.AssociatedWorkItem>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'author': {'key': 'author', 'type': 'IdentityRef'},
        'changeset_id': {'key': 'changesetId', 'type': 'int'},
        'checked_in_by': {'key': 'checkedInBy', 'type': 'IdentityRef'},
        'comment': {'key': 'comment', 'type': 'str'},
        'comment_truncated': {'key': 'commentTruncated', 'type': 'bool'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'url': {'key': 'url', 'type': 'str'},
        'account_id': {'key': 'accountId', 'type': 'str'},
        'changes': {'key': 'changes', 'type': '[TfvcChange]'},
        'checkin_notes': {'key': 'checkinNotes', 'type': '[CheckinNote]'},
        'collection_id': {'key': 'collectionId', 'type': 'str'},
        'has_more_changes': {'key': 'hasMoreChanges', 'type': 'bool'},
        'policy_override': {'key': 'policyOverride', 'type': 'TfvcPolicyOverrideInfo'},
        'team_project_ids': {'key': 'teamProjectIds', 'type': '[str]'},
        'work_items': {'key': 'workItems', 'type': '[AssociatedWorkItem]'}
    }

    def __init__(self, _links=None, author=None, changeset_id=None, checked_in_by=None, comment=None, comment_truncated=None, created_date=None, url=None, account_id=None, changes=None, checkin_notes=None, collection_id=None, has_more_changes=None, policy_override=None, team_project_ids=None, work_items=None):
        super(TfvcChangeset, self).__init__(_links=_links, author=author, changeset_id=changeset_id, checked_in_by=checked_in_by, comment=comment, comment_truncated=comment_truncated, created_date=created_date, url=url)
        self.account_id = account_id
        self.changes = changes
        self.checkin_notes = checkin_notes
        self.collection_id = collection_id
        self.has_more_changes = has_more_changes
        self.policy_override = policy_override
        self.team_project_ids = team_project_ids
        self.work_items = work_items
