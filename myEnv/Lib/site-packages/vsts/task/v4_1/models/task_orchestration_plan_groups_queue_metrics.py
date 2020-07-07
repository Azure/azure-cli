# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskOrchestrationPlanGroupsQueueMetrics(Model):
    """TaskOrchestrationPlanGroupsQueueMetrics.

    :param count:
    :type count: int
    :param status:
    :type status: object
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, count=None, status=None):
        super(TaskOrchestrationPlanGroupsQueueMetrics, self).__init__()
        self.count = count
        self.status = status
