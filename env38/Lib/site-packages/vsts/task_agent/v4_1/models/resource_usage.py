# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ResourceUsage(Model):
    """ResourceUsage.

    :param running_plan_groups:
    :type running_plan_groups: list of :class:`TaskOrchestrationPlanGroup <task-agent.v4_1.models.TaskOrchestrationPlanGroup>`
    :param total_count:
    :type total_count: int
    :param used_count:
    :type used_count: int
    """

    _attribute_map = {
        'running_plan_groups': {'key': 'runningPlanGroups', 'type': '[TaskOrchestrationPlanGroup]'},
        'total_count': {'key': 'totalCount', 'type': 'int'},
        'used_count': {'key': 'usedCount', 'type': 'int'}
    }

    def __init__(self, running_plan_groups=None, total_count=None, used_count=None):
        super(ResourceUsage, self).__init__()
        self.running_plan_groups = running_plan_groups
        self.total_count = total_count
        self.used_count = used_count
