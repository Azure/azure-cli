# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskOrchestrationQueuedPlan(Model):
    """TaskOrchestrationQueuedPlan.

    :param assign_time:
    :type assign_time: datetime
    :param definition:
    :type definition: :class:`TaskOrchestrationOwner <task.v4_0.models.TaskOrchestrationOwner>`
    :param owner:
    :type owner: :class:`TaskOrchestrationOwner <task.v4_0.models.TaskOrchestrationOwner>`
    :param plan_group:
    :type plan_group: str
    :param plan_id:
    :type plan_id: str
    :param pool_id:
    :type pool_id: int
    :param queue_position:
    :type queue_position: int
    :param queue_time:
    :type queue_time: datetime
    :param scope_identifier:
    :type scope_identifier: str
    """

    _attribute_map = {
        'assign_time': {'key': 'assignTime', 'type': 'iso-8601'},
        'definition': {'key': 'definition', 'type': 'TaskOrchestrationOwner'},
        'owner': {'key': 'owner', 'type': 'TaskOrchestrationOwner'},
        'plan_group': {'key': 'planGroup', 'type': 'str'},
        'plan_id': {'key': 'planId', 'type': 'str'},
        'pool_id': {'key': 'poolId', 'type': 'int'},
        'queue_position': {'key': 'queuePosition', 'type': 'int'},
        'queue_time': {'key': 'queueTime', 'type': 'iso-8601'},
        'scope_identifier': {'key': 'scopeIdentifier', 'type': 'str'}
    }

    def __init__(self, assign_time=None, definition=None, owner=None, plan_group=None, plan_id=None, pool_id=None, queue_position=None, queue_time=None, scope_identifier=None):
        super(TaskOrchestrationQueuedPlan, self).__init__()
        self.assign_time = assign_time
        self.definition = definition
        self.owner = owner
        self.plan_group = plan_group
        self.plan_id = plan_id
        self.pool_id = pool_id
        self.queue_position = queue_position
        self.queue_time = queue_time
        self.scope_identifier = scope_identifier
