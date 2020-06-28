# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .task_orchestration_item import TaskOrchestrationItem


class TaskOrchestrationContainer(TaskOrchestrationItem):
    """TaskOrchestrationContainer.

    :param item_type:
    :type item_type: object
    :param children:
    :type children: list of :class:`TaskOrchestrationItem <task.v4_1.models.TaskOrchestrationItem>`
    :param continue_on_error:
    :type continue_on_error: bool
    :param data:
    :type data: dict
    :param max_concurrency:
    :type max_concurrency: int
    :param parallel:
    :type parallel: bool
    :param rollback:
    :type rollback: :class:`TaskOrchestrationContainer <task.v4_1.models.TaskOrchestrationContainer>`
    """

    _attribute_map = {
        'item_type': {'key': 'itemType', 'type': 'object'},
        'children': {'key': 'children', 'type': '[TaskOrchestrationItem]'},
        'continue_on_error': {'key': 'continueOnError', 'type': 'bool'},
        'data': {'key': 'data', 'type': '{str}'},
        'max_concurrency': {'key': 'maxConcurrency', 'type': 'int'},
        'parallel': {'key': 'parallel', 'type': 'bool'},
        'rollback': {'key': 'rollback', 'type': 'TaskOrchestrationContainer'}
    }

    def __init__(self, item_type=None, children=None, continue_on_error=None, data=None, max_concurrency=None, parallel=None, rollback=None):
        super(TaskOrchestrationContainer, self).__init__(item_type=item_type)
        self.children = children
        self.continue_on_error = continue_on_error
        self.data = data
        self.max_concurrency = max_concurrency
        self.parallel = parallel
        self.rollback = rollback
