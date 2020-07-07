# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceEndpointExecutionData(Model):
    """ServiceEndpointExecutionData.

    :param definition: Gets the definition of service endpoint execution owner.
    :type definition: :class:`TaskOrchestrationOwner <task-agent.v4_1.models.TaskOrchestrationOwner>`
    :param finish_time: Gets the finish time of service endpoint execution.
    :type finish_time: datetime
    :param id: Gets the Id of service endpoint execution data.
    :type id: long
    :param owner: Gets the owner of service endpoint execution data.
    :type owner: :class:`TaskOrchestrationOwner <task-agent.v4_1.models.TaskOrchestrationOwner>`
    :param plan_type: Gets the plan type of service endpoint execution data.
    :type plan_type: str
    :param result: Gets the result of service endpoint execution.
    :type result: object
    :param start_time: Gets the start time of service endpoint execution.
    :type start_time: datetime
    """

    _attribute_map = {
        'definition': {'key': 'definition', 'type': 'TaskOrchestrationOwner'},
        'finish_time': {'key': 'finishTime', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'long'},
        'owner': {'key': 'owner', 'type': 'TaskOrchestrationOwner'},
        'plan_type': {'key': 'planType', 'type': 'str'},
        'result': {'key': 'result', 'type': 'object'},
        'start_time': {'key': 'startTime', 'type': 'iso-8601'}
    }

    def __init__(self, definition=None, finish_time=None, id=None, owner=None, plan_type=None, result=None, start_time=None):
        super(ServiceEndpointExecutionData, self).__init__()
        self.definition = definition
        self.finish_time = finish_time
        self.id = id
        self.owner = owner
        self.plan_type = plan_type
        self.result = result
        self.start_time = start_time
