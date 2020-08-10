# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentJobRequest(Model):
    """TaskAgentJobRequest.

    :param agent_delays:
    :type agent_delays: list of :class:`TaskAgentDelaySource <task-agent.v4_1.models.TaskAgentDelaySource>`
    :param assign_time:
    :type assign_time: datetime
    :param data:
    :type data: dict
    :param definition:
    :type definition: :class:`TaskOrchestrationOwner <task-agent.v4_1.models.TaskOrchestrationOwner>`
    :param demands:
    :type demands: list of :class:`object <task-agent.v4_1.models.object>`
    :param expected_duration:
    :type expected_duration: object
    :param finish_time:
    :type finish_time: datetime
    :param host_id:
    :type host_id: str
    :param job_id:
    :type job_id: str
    :param job_name:
    :type job_name: str
    :param locked_until:
    :type locked_until: datetime
    :param matched_agents:
    :type matched_agents: list of :class:`TaskAgentReference <task-agent.v4_1.models.TaskAgentReference>`
    :param owner:
    :type owner: :class:`TaskOrchestrationOwner <task-agent.v4_1.models.TaskOrchestrationOwner>`
    :param plan_group:
    :type plan_group: str
    :param plan_id:
    :type plan_id: str
    :param plan_type:
    :type plan_type: str
    :param pool_id:
    :type pool_id: int
    :param queue_id:
    :type queue_id: int
    :param queue_time:
    :type queue_time: datetime
    :param receive_time:
    :type receive_time: datetime
    :param request_id:
    :type request_id: long
    :param reserved_agent:
    :type reserved_agent: :class:`TaskAgentReference <task-agent.v4_1.models.TaskAgentReference>`
    :param result:
    :type result: object
    :param scope_id:
    :type scope_id: str
    :param service_owner:
    :type service_owner: str
    """

    _attribute_map = {
        'agent_delays': {'key': 'agentDelays', 'type': '[TaskAgentDelaySource]'},
        'assign_time': {'key': 'assignTime', 'type': 'iso-8601'},
        'data': {'key': 'data', 'type': '{str}'},
        'definition': {'key': 'definition', 'type': 'TaskOrchestrationOwner'},
        'demands': {'key': 'demands', 'type': '[object]'},
        'expected_duration': {'key': 'expectedDuration', 'type': 'object'},
        'finish_time': {'key': 'finishTime', 'type': 'iso-8601'},
        'host_id': {'key': 'hostId', 'type': 'str'},
        'job_id': {'key': 'jobId', 'type': 'str'},
        'job_name': {'key': 'jobName', 'type': 'str'},
        'locked_until': {'key': 'lockedUntil', 'type': 'iso-8601'},
        'matched_agents': {'key': 'matchedAgents', 'type': '[TaskAgentReference]'},
        'owner': {'key': 'owner', 'type': 'TaskOrchestrationOwner'},
        'plan_group': {'key': 'planGroup', 'type': 'str'},
        'plan_id': {'key': 'planId', 'type': 'str'},
        'plan_type': {'key': 'planType', 'type': 'str'},
        'pool_id': {'key': 'poolId', 'type': 'int'},
        'queue_id': {'key': 'queueId', 'type': 'int'},
        'queue_time': {'key': 'queueTime', 'type': 'iso-8601'},
        'receive_time': {'key': 'receiveTime', 'type': 'iso-8601'},
        'request_id': {'key': 'requestId', 'type': 'long'},
        'reserved_agent': {'key': 'reservedAgent', 'type': 'TaskAgentReference'},
        'result': {'key': 'result', 'type': 'object'},
        'scope_id': {'key': 'scopeId', 'type': 'str'},
        'service_owner': {'key': 'serviceOwner', 'type': 'str'}
    }

    def __init__(self, agent_delays=None, assign_time=None, data=None, definition=None, demands=None, expected_duration=None, finish_time=None, host_id=None, job_id=None, job_name=None, locked_until=None, matched_agents=None, owner=None, plan_group=None, plan_id=None, plan_type=None, pool_id=None, queue_id=None, queue_time=None, receive_time=None, request_id=None, reserved_agent=None, result=None, scope_id=None, service_owner=None):
        super(TaskAgentJobRequest, self).__init__()
        self.agent_delays = agent_delays
        self.assign_time = assign_time
        self.data = data
        self.definition = definition
        self.demands = demands
        self.expected_duration = expected_duration
        self.finish_time = finish_time
        self.host_id = host_id
        self.job_id = job_id
        self.job_name = job_name
        self.locked_until = locked_until
        self.matched_agents = matched_agents
        self.owner = owner
        self.plan_group = plan_group
        self.plan_id = plan_id
        self.plan_type = plan_type
        self.pool_id = pool_id
        self.queue_id = queue_id
        self.queue_time = queue_time
        self.receive_time = receive_time
        self.request_id = request_id
        self.reserved_agent = reserved_agent
        self.result = result
        self.scope_id = scope_id
        self.service_owner = service_owner
