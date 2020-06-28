# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ApprovalOptions(Model):
    """ApprovalOptions.

    :param auto_triggered_and_previous_environment_approved_can_be_skipped:
    :type auto_triggered_and_previous_environment_approved_can_be_skipped: bool
    :param enforce_identity_revalidation:
    :type enforce_identity_revalidation: bool
    :param release_creator_can_be_approver:
    :type release_creator_can_be_approver: bool
    :param required_approver_count:
    :type required_approver_count: int
    :param timeout_in_minutes:
    :type timeout_in_minutes: int
    """

    _attribute_map = {
        'auto_triggered_and_previous_environment_approved_can_be_skipped': {'key': 'autoTriggeredAndPreviousEnvironmentApprovedCanBeSkipped', 'type': 'bool'},
        'enforce_identity_revalidation': {'key': 'enforceIdentityRevalidation', 'type': 'bool'},
        'release_creator_can_be_approver': {'key': 'releaseCreatorCanBeApprover', 'type': 'bool'},
        'required_approver_count': {'key': 'requiredApproverCount', 'type': 'int'},
        'timeout_in_minutes': {'key': 'timeoutInMinutes', 'type': 'int'}
    }

    def __init__(self, auto_triggered_and_previous_environment_approved_can_be_skipped=None, enforce_identity_revalidation=None, release_creator_can_be_approver=None, required_approver_count=None, timeout_in_minutes=None):
        super(ApprovalOptions, self).__init__()
        self.auto_triggered_and_previous_environment_approved_can_be_skipped = auto_triggered_and_previous_environment_approved_can_be_skipped
        self.enforce_identity_revalidation = enforce_identity_revalidation
        self.release_creator_can_be_approver = release_creator_can_be_approver
        self.required_approver_count = required_approver_count
        self.timeout_in_minutes = timeout_in_minutes
