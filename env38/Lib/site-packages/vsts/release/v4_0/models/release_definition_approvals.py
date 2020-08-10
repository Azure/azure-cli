# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDefinitionApprovals(Model):
    """ReleaseDefinitionApprovals.

    :param approval_options:
    :type approval_options: :class:`ApprovalOptions <release.v4_0.models.ApprovalOptions>`
    :param approvals:
    :type approvals: list of :class:`ReleaseDefinitionApprovalStep <release.v4_0.models.ReleaseDefinitionApprovalStep>`
    """

    _attribute_map = {
        'approval_options': {'key': 'approvalOptions', 'type': 'ApprovalOptions'},
        'approvals': {'key': 'approvals', 'type': '[ReleaseDefinitionApprovalStep]'}
    }

    def __init__(self, approval_options=None, approvals=None):
        super(ReleaseDefinitionApprovals, self).__init__()
        self.approval_options = approval_options
        self.approvals = approvals
