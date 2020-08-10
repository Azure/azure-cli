# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .task_orchestration_plan_reference import TaskOrchestrationPlanReference


class TaskOrchestrationPlan(TaskOrchestrationPlanReference):
    """TaskOrchestrationPlan.

    :param artifact_location:
    :type artifact_location: str
    :param artifact_uri:
    :type artifact_uri: str
    :param definition:
    :type definition: :class:`TaskOrchestrationOwner <task.v4_0.models.TaskOrchestrationOwner>`
    :param owner:
    :type owner: :class:`TaskOrchestrationOwner <task.v4_0.models.TaskOrchestrationOwner>`
    :param plan_id:
    :type plan_id: str
    :param plan_type:
    :type plan_type: str
    :param scope_identifier:
    :type scope_identifier: str
    :param version:
    :type version: int
    :param environment:
    :type environment: :class:`PlanEnvironment <task.v4_0.models.PlanEnvironment>`
    :param finish_time:
    :type finish_time: datetime
    :param implementation:
    :type implementation: :class:`TaskOrchestrationContainer <task.v4_0.models.TaskOrchestrationContainer>`
    :param plan_group:
    :type plan_group: str
    :param requested_by_id:
    :type requested_by_id: str
    :param requested_for_id:
    :type requested_for_id: str
    :param result:
    :type result: object
    :param result_code:
    :type result_code: str
    :param start_time:
    :type start_time: datetime
    :param state:
    :type state: object
    :param timeline:
    :type timeline: :class:`TimelineReference <task.v4_0.models.TimelineReference>`
    """

    _attribute_map = {
        'artifact_location': {'key': 'artifactLocation', 'type': 'str'},
        'artifact_uri': {'key': 'artifactUri', 'type': 'str'},
        'definition': {'key': 'definition', 'type': 'TaskOrchestrationOwner'},
        'owner': {'key': 'owner', 'type': 'TaskOrchestrationOwner'},
        'plan_id': {'key': 'planId', 'type': 'str'},
        'plan_type': {'key': 'planType', 'type': 'str'},
        'scope_identifier': {'key': 'scopeIdentifier', 'type': 'str'},
        'version': {'key': 'version', 'type': 'int'},
        'environment': {'key': 'environment', 'type': 'PlanEnvironment'},
        'finish_time': {'key': 'finishTime', 'type': 'iso-8601'},
        'implementation': {'key': 'implementation', 'type': 'TaskOrchestrationContainer'},
        'plan_group': {'key': 'planGroup', 'type': 'str'},
        'requested_by_id': {'key': 'requestedById', 'type': 'str'},
        'requested_for_id': {'key': 'requestedForId', 'type': 'str'},
        'result': {'key': 'result', 'type': 'object'},
        'result_code': {'key': 'resultCode', 'type': 'str'},
        'start_time': {'key': 'startTime', 'type': 'iso-8601'},
        'state': {'key': 'state', 'type': 'object'},
        'timeline': {'key': 'timeline', 'type': 'TimelineReference'}
    }

    def __init__(self, artifact_location=None, artifact_uri=None, definition=None, owner=None, plan_id=None, plan_type=None, scope_identifier=None, version=None, environment=None, finish_time=None, implementation=None, plan_group=None, requested_by_id=None, requested_for_id=None, result=None, result_code=None, start_time=None, state=None, timeline=None):
        super(TaskOrchestrationPlan, self).__init__(artifact_location=artifact_location, artifact_uri=artifact_uri, definition=definition, owner=owner, plan_id=plan_id, plan_type=plan_type, scope_identifier=scope_identifier, version=version)
        self.environment = environment
        self.finish_time = finish_time
        self.implementation = implementation
        self.plan_group = plan_group
        self.requested_by_id = requested_by_id
        self.requested_for_id = requested_for_id
        self.result = result
        self.result_code = result_code
        self.start_time = start_time
        self.state = state
        self.timeline = timeline
