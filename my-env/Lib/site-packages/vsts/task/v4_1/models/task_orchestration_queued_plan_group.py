# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskOrchestrationQueuedPlanGroup(Model):
    """TaskOrchestrationQueuedPlanGroup.

    :param definition:
    :type definition: :class:`TaskOrchestrationOwner <task.v4_1.models.TaskOrchestrationOwner>`
    :param owner:
    :type owner: :class:`TaskOrchestrationOwner <task.v4_1.models.TaskOrchestrationOwner>`
    :param plan_group:
    :type plan_group: str
    :param plans:
    :type plans: list of :class:`TaskOrchestrationQueuedPlan <task.v4_1.models.TaskOrchestrationQueuedPlan>`
    :param project:
    :type project: :class:`ProjectReference <task.v4_1.models.ProjectReference>`
    :param queue_position:
    :type queue_position: int
    """

    _attribute_map = {
        'definition': {'key': 'definition', 'type': 'TaskOrchestrationOwner'},
        'owner': {'key': 'owner', 'type': 'TaskOrchestrationOwner'},
        'plan_group': {'key': 'planGroup', 'type': 'str'},
        'plans': {'key': 'plans', 'type': '[TaskOrchestrationQueuedPlan]'},
        'project': {'key': 'project', 'type': 'ProjectReference'},
        'queue_position': {'key': 'queuePosition', 'type': 'int'}
    }

    def __init__(self, definition=None, owner=None, plan_group=None, plans=None, project=None, queue_position=None):
        super(TaskOrchestrationQueuedPlanGroup, self).__init__()
        self.definition = definition
        self.owner = owner
        self.plan_group = plan_group
        self.plans = plans
        self.project = project
        self.queue_position = queue_position
