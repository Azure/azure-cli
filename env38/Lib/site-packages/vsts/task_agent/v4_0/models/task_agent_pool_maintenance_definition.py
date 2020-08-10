# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentPoolMaintenanceDefinition(Model):
    """TaskAgentPoolMaintenanceDefinition.

    :param enabled: Enable maintenance
    :type enabled: bool
    :param id: Id
    :type id: int
    :param job_timeout_in_minutes: Maintenance job timeout per agent
    :type job_timeout_in_minutes: int
    :param max_concurrent_agents_percentage: Max percentage of agents within a pool running maintenance job at given time
    :type max_concurrent_agents_percentage: int
    :param options:
    :type options: :class:`TaskAgentPoolMaintenanceOptions <task-agent.v4_0.models.TaskAgentPoolMaintenanceOptions>`
    :param pool: Pool reference for the maintenance definition
    :type pool: :class:`TaskAgentPoolReference <task-agent.v4_0.models.TaskAgentPoolReference>`
    :param retention_policy:
    :type retention_policy: :class:`TaskAgentPoolMaintenanceRetentionPolicy <task-agent.v4_0.models.TaskAgentPoolMaintenanceRetentionPolicy>`
    :param schedule_setting:
    :type schedule_setting: :class:`TaskAgentPoolMaintenanceSchedule <task-agent.v4_0.models.TaskAgentPoolMaintenanceSchedule>`
    """

    _attribute_map = {
        'enabled': {'key': 'enabled', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'int'},
        'job_timeout_in_minutes': {'key': 'jobTimeoutInMinutes', 'type': 'int'},
        'max_concurrent_agents_percentage': {'key': 'maxConcurrentAgentsPercentage', 'type': 'int'},
        'options': {'key': 'options', 'type': 'TaskAgentPoolMaintenanceOptions'},
        'pool': {'key': 'pool', 'type': 'TaskAgentPoolReference'},
        'retention_policy': {'key': 'retentionPolicy', 'type': 'TaskAgentPoolMaintenanceRetentionPolicy'},
        'schedule_setting': {'key': 'scheduleSetting', 'type': 'TaskAgentPoolMaintenanceSchedule'}
    }

    def __init__(self, enabled=None, id=None, job_timeout_in_minutes=None, max_concurrent_agents_percentage=None, options=None, pool=None, retention_policy=None, schedule_setting=None):
        super(TaskAgentPoolMaintenanceDefinition, self).__init__()
        self.enabled = enabled
        self.id = id
        self.job_timeout_in_minutes = job_timeout_in_minutes
        self.max_concurrent_agents_percentage = max_concurrent_agents_percentage
        self.options = options
        self.pool = pool
        self.retention_policy = retention_policy
        self.schedule_setting = schedule_setting
