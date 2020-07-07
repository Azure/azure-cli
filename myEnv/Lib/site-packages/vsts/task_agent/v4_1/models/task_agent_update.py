# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentUpdate(Model):
    """TaskAgentUpdate.

    :param current_state: The current state of this agent update
    :type current_state: str
    :param reason: The reason of this agent update
    :type reason: :class:`TaskAgentUpdateReason <task-agent.v4_1.models.TaskAgentUpdateReason>`
    :param requested_by: The identity that request the agent update
    :type requested_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param request_time: Gets the date on which this agent update was requested.
    :type request_time: datetime
    :param source_version: Gets or sets the source agent version of the agent update
    :type source_version: :class:`PackageVersion <task-agent.v4_1.models.PackageVersion>`
    :param target_version: Gets or sets the target agent version of the agent update
    :type target_version: :class:`PackageVersion <task-agent.v4_1.models.PackageVersion>`
    """

    _attribute_map = {
        'current_state': {'key': 'currentState', 'type': 'str'},
        'reason': {'key': 'reason', 'type': 'TaskAgentUpdateReason'},
        'requested_by': {'key': 'requestedBy', 'type': 'IdentityRef'},
        'request_time': {'key': 'requestTime', 'type': 'iso-8601'},
        'source_version': {'key': 'sourceVersion', 'type': 'PackageVersion'},
        'target_version': {'key': 'targetVersion', 'type': 'PackageVersion'}
    }

    def __init__(self, current_state=None, reason=None, requested_by=None, request_time=None, source_version=None, target_version=None):
        super(TaskAgentUpdate, self).__init__()
        self.current_state = current_state
        self.reason = reason
        self.requested_by = requested_by
        self.request_time = request_time
        self.source_version = source_version
        self.target_version = target_version
