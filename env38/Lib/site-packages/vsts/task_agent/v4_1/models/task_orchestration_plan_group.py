# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskOrchestrationPlanGroup(Model):
    """TaskOrchestrationPlanGroup.

    :param plan_group:
    :type plan_group: str
    :param project:
    :type project: :class:`ProjectReference <task-agent.v4_1.models.ProjectReference>`
    :param running_requests:
    :type running_requests: list of :class:`TaskAgentJobRequest <task-agent.v4_1.models.TaskAgentJobRequest>`
    """

    _attribute_map = {
        'plan_group': {'key': 'planGroup', 'type': 'str'},
        'project': {'key': 'project', 'type': 'ProjectReference'},
        'running_requests': {'key': 'runningRequests', 'type': '[TaskAgentJobRequest]'}
    }

    def __init__(self, plan_group=None, project=None, running_requests=None):
        super(TaskOrchestrationPlanGroup, self).__init__()
        self.plan_group = plan_group
        self.project = project
        self.running_requests = running_requests
