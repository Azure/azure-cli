# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProjectWorkItemStateColors(Model):
    """ProjectWorkItemStateColors.

    :param project_name: Project name
    :type project_name: str
    :param work_item_type_state_colors: State colors for all work item type in a project
    :type work_item_type_state_colors: list of :class:`WorkItemTypeStateColors <work-item-tracking.v4_0.models.WorkItemTypeStateColors>`
    """

    _attribute_map = {
        'project_name': {'key': 'projectName', 'type': 'str'},
        'work_item_type_state_colors': {'key': 'workItemTypeStateColors', 'type': '[WorkItemTypeStateColors]'}
    }

    def __init__(self, project_name=None, work_item_type_state_colors=None):
        super(ProjectWorkItemStateColors, self).__init__()
        self.project_name = project_name
        self.work_item_type_state_colors = work_item_type_state_colors
