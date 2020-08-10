# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentPoolMaintenanceJob(Model):
    """TaskAgentPoolMaintenanceJob.

    :param definition_id: The maintenance definition for the maintenance job
    :type definition_id: int
    :param error_count: The total error counts during the maintenance job
    :type error_count: int
    :param finish_time: Time that the maintenance job was completed
    :type finish_time: datetime
    :param job_id: Id of the maintenance job
    :type job_id: int
    :param logs_download_url: The log download url for the maintenance job
    :type logs_download_url: str
    :param orchestration_id: Orchestration/Plan Id for the maintenance job
    :type orchestration_id: str
    :param pool: Pool reference for the maintenance job
    :type pool: :class:`TaskAgentPoolReference <task-agent.v4_1.models.TaskAgentPoolReference>`
    :param queue_time: Time that the maintenance job was queued
    :type queue_time: datetime
    :param requested_by: The identity that queued the maintenance job
    :type requested_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param result: The maintenance job result
    :type result: object
    :param start_time: Time that the maintenance job was started
    :type start_time: datetime
    :param status: Status of the maintenance job
    :type status: object
    :param target_agents:
    :type target_agents: list of :class:`TaskAgentPoolMaintenanceJobTargetAgent <task-agent.v4_1.models.TaskAgentPoolMaintenanceJobTargetAgent>`
    :param warning_count: The total warning counts during the maintenance job
    :type warning_count: int
    """

    _attribute_map = {
        'definition_id': {'key': 'definitionId', 'type': 'int'},
        'error_count': {'key': 'errorCount', 'type': 'int'},
        'finish_time': {'key': 'finishTime', 'type': 'iso-8601'},
        'job_id': {'key': 'jobId', 'type': 'int'},
        'logs_download_url': {'key': 'logsDownloadUrl', 'type': 'str'},
        'orchestration_id': {'key': 'orchestrationId', 'type': 'str'},
        'pool': {'key': 'pool', 'type': 'TaskAgentPoolReference'},
        'queue_time': {'key': 'queueTime', 'type': 'iso-8601'},
        'requested_by': {'key': 'requestedBy', 'type': 'IdentityRef'},
        'result': {'key': 'result', 'type': 'object'},
        'start_time': {'key': 'startTime', 'type': 'iso-8601'},
        'status': {'key': 'status', 'type': 'object'},
        'target_agents': {'key': 'targetAgents', 'type': '[TaskAgentPoolMaintenanceJobTargetAgent]'},
        'warning_count': {'key': 'warningCount', 'type': 'int'}
    }

    def __init__(self, definition_id=None, error_count=None, finish_time=None, job_id=None, logs_download_url=None, orchestration_id=None, pool=None, queue_time=None, requested_by=None, result=None, start_time=None, status=None, target_agents=None, warning_count=None):
        super(TaskAgentPoolMaintenanceJob, self).__init__()
        self.definition_id = definition_id
        self.error_count = error_count
        self.finish_time = finish_time
        self.job_id = job_id
        self.logs_download_url = logs_download_url
        self.orchestration_id = orchestration_id
        self.pool = pool
        self.queue_time = queue_time
        self.requested_by = requested_by
        self.result = result
        self.start_time = start_time
        self.status = status
        self.target_agents = target_agents
        self.warning_count = warning_count
