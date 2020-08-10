# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseApproval(Model):
    """ReleaseApproval.

    :param approval_type: Gets or sets the type of approval.
    :type approval_type: object
    :param approved_by: Gets the identity who approved.
    :type approved_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param approver: Gets or sets the identity who should approve.
    :type approver: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param attempt: Gets or sets attempt which specifies as which deployment attempt it belongs.
    :type attempt: int
    :param comments: Gets or sets comments for approval.
    :type comments: str
    :param created_on: Gets date on which it got created.
    :type created_on: datetime
    :param history: Gets history which specifies all approvals associated with this approval.
    :type history: list of :class:`ReleaseApprovalHistory <release.v4_0.models.ReleaseApprovalHistory>`
    :param id: Gets the unique identifier of this field.
    :type id: int
    :param is_automated: Gets or sets as approval is automated or not.
    :type is_automated: bool
    :param is_notification_on:
    :type is_notification_on: bool
    :param modified_on: Gets date on which it got modified.
    :type modified_on: datetime
    :param rank: Gets or sets rank which specifies the order of the approval. e.g. Same rank denotes parallel approval.
    :type rank: int
    :param release: Gets releaseReference which specifies the reference of the release to which this approval is associated.
    :type release: :class:`ReleaseShallowReference <release.v4_0.models.ReleaseShallowReference>`
    :param release_definition: Gets releaseDefinitionReference which specifies the reference of the release definition to which this approval is associated.
    :type release_definition: :class:`ReleaseDefinitionShallowReference <release.v4_0.models.ReleaseDefinitionShallowReference>`
    :param release_environment: Gets releaseEnvironmentReference which specifies the reference of the release environment to which this approval is associated.
    :type release_environment: :class:`ReleaseEnvironmentShallowReference <release.v4_0.models.ReleaseEnvironmentShallowReference>`
    :param revision: Gets the revision number.
    :type revision: int
    :param status: Gets or sets the status of the approval.
    :type status: object
    :param trial_number:
    :type trial_number: int
    :param url: Gets url to access the approval.
    :type url: str
    """

    _attribute_map = {
        'approval_type': {'key': 'approvalType', 'type': 'object'},
        'approved_by': {'key': 'approvedBy', 'type': 'IdentityRef'},
        'approver': {'key': 'approver', 'type': 'IdentityRef'},
        'attempt': {'key': 'attempt', 'type': 'int'},
        'comments': {'key': 'comments', 'type': 'str'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'history': {'key': 'history', 'type': '[ReleaseApprovalHistory]'},
        'id': {'key': 'id', 'type': 'int'},
        'is_automated': {'key': 'isAutomated', 'type': 'bool'},
        'is_notification_on': {'key': 'isNotificationOn', 'type': 'bool'},
        'modified_on': {'key': 'modifiedOn', 'type': 'iso-8601'},
        'rank': {'key': 'rank', 'type': 'int'},
        'release': {'key': 'release', 'type': 'ReleaseShallowReference'},
        'release_definition': {'key': 'releaseDefinition', 'type': 'ReleaseDefinitionShallowReference'},
        'release_environment': {'key': 'releaseEnvironment', 'type': 'ReleaseEnvironmentShallowReference'},
        'revision': {'key': 'revision', 'type': 'int'},
        'status': {'key': 'status', 'type': 'object'},
        'trial_number': {'key': 'trialNumber', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, approval_type=None, approved_by=None, approver=None, attempt=None, comments=None, created_on=None, history=None, id=None, is_automated=None, is_notification_on=None, modified_on=None, rank=None, release=None, release_definition=None, release_environment=None, revision=None, status=None, trial_number=None, url=None):
        super(ReleaseApproval, self).__init__()
        self.approval_type = approval_type
        self.approved_by = approved_by
        self.approver = approver
        self.attempt = attempt
        self.comments = comments
        self.created_on = created_on
        self.history = history
        self.id = id
        self.is_automated = is_automated
        self.is_notification_on = is_notification_on
        self.modified_on = modified_on
        self.rank = rank
        self.release = release
        self.release_definition = release_definition
        self.release_environment = release_environment
        self.revision = revision
        self.status = status
        self.trial_number = trial_number
        self.url = url
