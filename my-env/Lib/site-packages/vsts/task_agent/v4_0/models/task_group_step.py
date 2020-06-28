# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskGroupStep(Model):
    """TaskGroupStep.

    :param always_run: Gets or sets as 'true' to run the task always, 'false' otherwise.
    :type always_run: bool
    :param condition:
    :type condition: str
    :param continue_on_error: Gets or sets as 'true' to continue on error, 'false' otherwise.
    :type continue_on_error: bool
    :param display_name: Gets or sets the display name.
    :type display_name: str
    :param enabled: Gets or sets as task is enabled or not.
    :type enabled: bool
    :param inputs: Gets or sets dictionary of inputs.
    :type inputs: dict
    :param task: Gets or sets the reference of the task.
    :type task: :class:`TaskDefinitionReference <task-agent.v4_0.models.TaskDefinitionReference>`
    :param timeout_in_minutes: Gets or sets the maximum time, in minutes, that a task is allowed to execute on agent before being cancelled by server. A zero value indicates an infinite timeout.
    :type timeout_in_minutes: int
    """

    _attribute_map = {
        'always_run': {'key': 'alwaysRun', 'type': 'bool'},
        'condition': {'key': 'condition', 'type': 'str'},
        'continue_on_error': {'key': 'continueOnError', 'type': 'bool'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'enabled': {'key': 'enabled', 'type': 'bool'},
        'inputs': {'key': 'inputs', 'type': '{str}'},
        'task': {'key': 'task', 'type': 'TaskDefinitionReference'},
        'timeout_in_minutes': {'key': 'timeoutInMinutes', 'type': 'int'}
    }

    def __init__(self, always_run=None, condition=None, continue_on_error=None, display_name=None, enabled=None, inputs=None, task=None, timeout_in_minutes=None):
        super(TaskGroupStep, self).__init__()
        self.always_run = always_run
        self.condition = condition
        self.continue_on_error = continue_on_error
        self.display_name = display_name
        self.enabled = enabled
        self.inputs = inputs
        self.task = task
        self.timeout_in_minutes = timeout_in_minutes
