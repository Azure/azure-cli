# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkflowTask(Model):
    """WorkflowTask.

    :param always_run:
    :type always_run: bool
    :param condition:
    :type condition: str
    :param continue_on_error:
    :type continue_on_error: bool
    :param definition_type:
    :type definition_type: str
    :param enabled:
    :type enabled: bool
    :param inputs:
    :type inputs: dict
    :param name:
    :type name: str
    :param override_inputs:
    :type override_inputs: dict
    :param ref_name:
    :type ref_name: str
    :param task_id:
    :type task_id: str
    :param timeout_in_minutes:
    :type timeout_in_minutes: int
    :param version:
    :type version: str
    """

    _attribute_map = {
        'always_run': {'key': 'alwaysRun', 'type': 'bool'},
        'condition': {'key': 'condition', 'type': 'str'},
        'continue_on_error': {'key': 'continueOnError', 'type': 'bool'},
        'definition_type': {'key': 'definitionType', 'type': 'str'},
        'enabled': {'key': 'enabled', 'type': 'bool'},
        'inputs': {'key': 'inputs', 'type': '{str}'},
        'name': {'key': 'name', 'type': 'str'},
        'override_inputs': {'key': 'overrideInputs', 'type': '{str}'},
        'ref_name': {'key': 'refName', 'type': 'str'},
        'task_id': {'key': 'taskId', 'type': 'str'},
        'timeout_in_minutes': {'key': 'timeoutInMinutes', 'type': 'int'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, always_run=None, condition=None, continue_on_error=None, definition_type=None, enabled=None, inputs=None, name=None, override_inputs=None, ref_name=None, task_id=None, timeout_in_minutes=None, version=None):
        super(WorkflowTask, self).__init__()
        self.always_run = always_run
        self.condition = condition
        self.continue_on_error = continue_on_error
        self.definition_type = definition_type
        self.enabled = enabled
        self.inputs = inputs
        self.name = name
        self.override_inputs = override_inputs
        self.ref_name = ref_name
        self.task_id = task_id
        self.timeout_in_minutes = timeout_in_minutes
        self.version = version
