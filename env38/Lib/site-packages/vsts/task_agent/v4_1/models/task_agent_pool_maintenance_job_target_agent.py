# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentPoolMaintenanceJobTargetAgent(Model):
    """TaskAgentPoolMaintenanceJobTargetAgent.

    :param agent:
    :type agent: :class:`TaskAgentReference <task-agent.v4_1.models.TaskAgentReference>`
    :param job_id:
    :type job_id: int
    :param result:
    :type result: object
    :param status:
    :type status: object
    """

    _attribute_map = {
        'agent': {'key': 'agent', 'type': 'TaskAgentReference'},
        'job_id': {'key': 'jobId', 'type': 'int'},
        'result': {'key': 'result', 'type': 'object'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, agent=None, job_id=None, result=None, status=None):
        super(TaskAgentPoolMaintenanceJobTargetAgent, self).__init__()
        self.agent = agent
        self.job_id = job_id
        self.result = result
        self.status = status
