# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseRevision(Model):
    """ReleaseRevision.

    :param changed_by:
    :type changed_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param changed_date:
    :type changed_date: datetime
    :param change_details:
    :type change_details: str
    :param change_type:
    :type change_type: str
    :param comment:
    :type comment: str
    :param definition_snapshot_revision:
    :type definition_snapshot_revision: int
    :param release_id:
    :type release_id: int
    """

    _attribute_map = {
        'changed_by': {'key': 'changedBy', 'type': 'IdentityRef'},
        'changed_date': {'key': 'changedDate', 'type': 'iso-8601'},
        'change_details': {'key': 'changeDetails', 'type': 'str'},
        'change_type': {'key': 'changeType', 'type': 'str'},
        'comment': {'key': 'comment', 'type': 'str'},
        'definition_snapshot_revision': {'key': 'definitionSnapshotRevision', 'type': 'int'},
        'release_id': {'key': 'releaseId', 'type': 'int'}
    }

    def __init__(self, changed_by=None, changed_date=None, change_details=None, change_type=None, comment=None, definition_snapshot_revision=None, release_id=None):
        super(ReleaseRevision, self).__init__()
        self.changed_by = changed_by
        self.changed_date = changed_date
        self.change_details = change_details
        self.change_type = change_type
        self.comment = comment
        self.definition_snapshot_revision = definition_snapshot_revision
        self.release_id = release_id
