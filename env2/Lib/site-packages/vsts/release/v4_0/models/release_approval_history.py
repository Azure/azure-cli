# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseApprovalHistory(Model):
    """ReleaseApprovalHistory.

    :param approver:
    :type approver: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param changed_by:
    :type changed_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param comments:
    :type comments: str
    :param created_on:
    :type created_on: datetime
    :param modified_on:
    :type modified_on: datetime
    :param revision:
    :type revision: int
    """

    _attribute_map = {
        'approver': {'key': 'approver', 'type': 'IdentityRef'},
        'changed_by': {'key': 'changedBy', 'type': 'IdentityRef'},
        'comments': {'key': 'comments', 'type': 'str'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'modified_on': {'key': 'modifiedOn', 'type': 'iso-8601'},
        'revision': {'key': 'revision', 'type': 'int'}
    }

    def __init__(self, approver=None, changed_by=None, comments=None, created_on=None, modified_on=None, revision=None):
        super(ReleaseApprovalHistory, self).__init__()
        self.approver = approver
        self.changed_by = changed_by
        self.comments = comments
        self.created_on = created_on
        self.modified_on = modified_on
        self.revision = revision
