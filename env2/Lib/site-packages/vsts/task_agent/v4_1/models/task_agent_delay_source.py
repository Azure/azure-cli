# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentDelaySource(Model):
    """TaskAgentDelaySource.

    :param delays:
    :type delays: list of object
    :param task_agent:
    :type task_agent: :class:`TaskAgentReference <task-agent.v4_1.models.TaskAgentReference>`
    """

    _attribute_map = {
        'delays': {'key': 'delays', 'type': '[object]'},
        'task_agent': {'key': 'taskAgent', 'type': 'TaskAgentReference'}
    }

    def __init__(self, delays=None, task_agent=None):
        super(TaskAgentDelaySource, self).__init__()
        self.delays = delays
        self.task_agent = task_agent
