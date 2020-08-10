# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .task_agent_reference import TaskAgentReference


class TaskAgent(TaskAgentReference):
    """TaskAgent.

    :param _links:
    :type _links: :class:`ReferenceLinks <task-agent.v4_1.models.ReferenceLinks>`
    :param enabled: Gets or sets a value indicating whether or not this agent should be enabled for job execution.
    :type enabled: bool
    :param id: Gets the identifier of the agent.
    :type id: int
    :param name: Gets the name of the agent.
    :type name: str
    :param oSDescription: Gets the OS of the agent.
    :type oSDescription: str
    :param status: Gets the current connectivity status of the agent.
    :type status: object
    :param version: Gets the version of the agent.
    :type version: str
    :param assigned_request: Gets the request which is currently assigned to this agent.
    :type assigned_request: :class:`TaskAgentJobRequest <task-agent.v4_1.models.TaskAgentJobRequest>`
    :param authorization: Gets or sets the authorization information for this agent.
    :type authorization: :class:`TaskAgentAuthorization <task-agent.v4_1.models.TaskAgentAuthorization>`
    :param created_on: Gets the date on which this agent was created.
    :type created_on: datetime
    :param last_completed_request: Gets the last request which was completed by this agent.
    :type last_completed_request: :class:`TaskAgentJobRequest <task-agent.v4_1.models.TaskAgentJobRequest>`
    :param max_parallelism: Gets or sets the maximum job parallelism allowed on this host.
    :type max_parallelism: int
    :param pending_update: Gets the pending update for this agent.
    :type pending_update: :class:`TaskAgentUpdate <task-agent.v4_1.models.TaskAgentUpdate>`
    :param properties:
    :type properties: :class:`object <task-agent.v4_1.models.object>`
    :param status_changed_on: Gets the date on which the last connectivity status change occurred.
    :type status_changed_on: datetime
    :param system_capabilities:
    :type system_capabilities: dict
    :param user_capabilities:
    :type user_capabilities: dict
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'enabled': {'key': 'enabled', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'oSDescription': {'key': 'oSDescription', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'version': {'key': 'version', 'type': 'str'},
        'assigned_request': {'key': 'assignedRequest', 'type': 'TaskAgentJobRequest'},
        'authorization': {'key': 'authorization', 'type': 'TaskAgentAuthorization'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'last_completed_request': {'key': 'lastCompletedRequest', 'type': 'TaskAgentJobRequest'},
        'max_parallelism': {'key': 'maxParallelism', 'type': 'int'},
        'pending_update': {'key': 'pendingUpdate', 'type': 'TaskAgentUpdate'},
        'properties': {'key': 'properties', 'type': 'object'},
        'status_changed_on': {'key': 'statusChangedOn', 'type': 'iso-8601'},
        'system_capabilities': {'key': 'systemCapabilities', 'type': '{str}'},
        'user_capabilities': {'key': 'userCapabilities', 'type': '{str}'}
    }

    def __init__(self, _links=None, enabled=None, id=None, name=None, oSDescription=None, status=None, version=None, assigned_request=None, authorization=None, created_on=None, last_completed_request=None, max_parallelism=None, pending_update=None, properties=None, status_changed_on=None, system_capabilities=None, user_capabilities=None):
        super(TaskAgent, self).__init__(_links=_links, enabled=enabled, id=id, name=name, oSDescription=oSDescription, status=status, version=version)
        self.assigned_request = assigned_request
        self.authorization = authorization
        self.created_on = created_on
        self.last_completed_request = last_completed_request
        self.max_parallelism = max_parallelism
        self.pending_update = pending_update
        self.properties = properties
        self.status_changed_on = status_changed_on
        self.system_capabilities = system_capabilities
        self.user_capabilities = user_capabilities
