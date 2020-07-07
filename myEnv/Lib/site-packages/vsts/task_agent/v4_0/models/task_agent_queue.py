# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentQueue(Model):
    """TaskAgentQueue.

    :param id:
    :type id: int
    :param name:
    :type name: str
    :param pool:
    :type pool: :class:`TaskAgentPoolReference <task-agent.v4_0.models.TaskAgentPoolReference>`
    :param project_id:
    :type project_id: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'pool': {'key': 'pool', 'type': 'TaskAgentPoolReference'},
        'project_id': {'key': 'projectId', 'type': 'str'}
    }

    def __init__(self, id=None, name=None, pool=None, project_id=None):
        super(TaskAgentQueue, self).__init__()
        self.id = id
        self.name = name
        self.pool = pool
        self.project_id = project_id
