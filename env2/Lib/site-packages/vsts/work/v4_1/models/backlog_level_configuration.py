# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BacklogLevelConfiguration(Model):
    """BacklogLevelConfiguration.

    :param add_panel_fields: List of fields to include in Add Panel
    :type add_panel_fields: list of :class:`WorkItemFieldReference <work.v4_1.models.WorkItemFieldReference>`
    :param color: Color for the backlog level
    :type color: str
    :param column_fields: Default list of columns for the backlog
    :type column_fields: list of :class:`BacklogColumn <work.v4_1.models.BacklogColumn>`
    :param default_work_item_type: Defaulst Work Item Type for the backlog
    :type default_work_item_type: :class:`WorkItemTypeReference <work.v4_1.models.WorkItemTypeReference>`
    :param id: Backlog Id (for Legacy Backlog Level from process config it can be categoryref name)
    :type id: str
    :param is_hidden: Indicates whether the backlog level is hidden
    :type is_hidden: bool
    :param name: Backlog Name
    :type name: str
    :param rank: Backlog Rank (Taskbacklog is 0)
    :type rank: int
    :param type: The type of this backlog level
    :type type: object
    :param work_item_count_limit: Max number of work items to show in the given backlog
    :type work_item_count_limit: int
    :param work_item_types: Work Item types participating in this backlog as known by the project/Process, can be overridden by team settings for bugs
    :type work_item_types: list of :class:`WorkItemTypeReference <work.v4_1.models.WorkItemTypeReference>`
    """

    _attribute_map = {
        'add_panel_fields': {'key': 'addPanelFields', 'type': '[WorkItemFieldReference]'},
        'color': {'key': 'color', 'type': 'str'},
        'column_fields': {'key': 'columnFields', 'type': '[BacklogColumn]'},
        'default_work_item_type': {'key': 'defaultWorkItemType', 'type': 'WorkItemTypeReference'},
        'id': {'key': 'id', 'type': 'str'},
        'is_hidden': {'key': 'isHidden', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'rank': {'key': 'rank', 'type': 'int'},
        'type': {'key': 'type', 'type': 'object'},
        'work_item_count_limit': {'key': 'workItemCountLimit', 'type': 'int'},
        'work_item_types': {'key': 'workItemTypes', 'type': '[WorkItemTypeReference]'}
    }

    def __init__(self, add_panel_fields=None, color=None, column_fields=None, default_work_item_type=None, id=None, is_hidden=None, name=None, rank=None, type=None, work_item_count_limit=None, work_item_types=None):
        super(BacklogLevelConfiguration, self).__init__()
        self.add_panel_fields = add_panel_fields
        self.color = color
        self.column_fields = column_fields
        self.default_work_item_type = default_work_item_type
        self.id = id
        self.is_hidden = is_hidden
        self.name = name
        self.rank = rank
        self.type = type
        self.work_item_count_limit = work_item_count_limit
        self.work_item_types = work_item_types
