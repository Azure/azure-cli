# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .release_definition_environment_step import ReleaseDefinitionEnvironmentStep


class ReleaseDefinitionApprovalStep(ReleaseDefinitionEnvironmentStep):
    """ReleaseDefinitionApprovalStep.

    :param id:
    :type id: int
    :param approver:
    :type approver: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param is_automated:
    :type is_automated: bool
    :param is_notification_on:
    :type is_notification_on: bool
    :param rank:
    :type rank: int
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'approver': {'key': 'approver', 'type': 'IdentityRef'},
        'is_automated': {'key': 'isAutomated', 'type': 'bool'},
        'is_notification_on': {'key': 'isNotificationOn', 'type': 'bool'},
        'rank': {'key': 'rank', 'type': 'int'}
    }

    def __init__(self, id=None, approver=None, is_automated=None, is_notification_on=None, rank=None):
        super(ReleaseDefinitionApprovalStep, self).__init__(id=id)
        self.approver = approver
        self.is_automated = is_automated
        self.is_notification_on = is_notification_on
        self.rank = rank
