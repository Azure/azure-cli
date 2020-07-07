# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TimelineTeamData(Model):
    """TimelineTeamData.

    :param backlog: Backlog matching the mapped backlog associated with this team.
    :type backlog: :class:`BacklogLevel <work.v4_0.models.BacklogLevel>`
    :param field_reference_names: The field reference names of the work item data
    :type field_reference_names: list of str
    :param id: The id of the team
    :type id: str
    :param is_expanded: Was iteration and work item data retrieved for this team. <remarks> Teams with IsExpanded false have not had their iteration, work item, and field related data queried and will never contain this data. If true then these items are queried and, if there are items in the queried range, there will be data. </remarks>
    :type is_expanded: bool
    :param iterations: The iteration data, including the work items, in the queried date range.
    :type iterations: list of :class:`TimelineTeamIteration <work.v4_0.models.TimelineTeamIteration>`
    :param name: The name of the team
    :type name: str
    :param order_by_field: The order by field name of this team
    :type order_by_field: str
    :param partially_paged_field_reference_names: The field reference names of the partially paged work items, such as ID, WorkItemType
    :type partially_paged_field_reference_names: list of str
    :param project_id: The project id the team belongs team
    :type project_id: str
    :param status: Status for this team.
    :type status: :class:`TimelineTeamStatus <work.v4_0.models.TimelineTeamStatus>`
    :param team_field_default_value: The team field default value
    :type team_field_default_value: str
    :param team_field_name: The team field name of this team
    :type team_field_name: str
    :param team_field_values: The team field values
    :type team_field_values: list of :class:`TeamFieldValue <work.v4_0.models.TeamFieldValue>`
    :param work_item_type_colors: Colors for the work item types.
    :type work_item_type_colors: list of :class:`WorkItemColor <work.v4_0.models.WorkItemColor>`
    """

    _attribute_map = {
        'backlog': {'key': 'backlog', 'type': 'BacklogLevel'},
        'field_reference_names': {'key': 'fieldReferenceNames', 'type': '[str]'},
        'id': {'key': 'id', 'type': 'str'},
        'is_expanded': {'key': 'isExpanded', 'type': 'bool'},
        'iterations': {'key': 'iterations', 'type': '[TimelineTeamIteration]'},
        'name': {'key': 'name', 'type': 'str'},
        'order_by_field': {'key': 'orderByField', 'type': 'str'},
        'partially_paged_field_reference_names': {'key': 'partiallyPagedFieldReferenceNames', 'type': '[str]'},
        'project_id': {'key': 'projectId', 'type': 'str'},
        'status': {'key': 'status', 'type': 'TimelineTeamStatus'},
        'team_field_default_value': {'key': 'teamFieldDefaultValue', 'type': 'str'},
        'team_field_name': {'key': 'teamFieldName', 'type': 'str'},
        'team_field_values': {'key': 'teamFieldValues', 'type': '[TeamFieldValue]'},
        'work_item_type_colors': {'key': 'workItemTypeColors', 'type': '[WorkItemColor]'}
    }

    def __init__(self, backlog=None, field_reference_names=None, id=None, is_expanded=None, iterations=None, name=None, order_by_field=None, partially_paged_field_reference_names=None, project_id=None, status=None, team_field_default_value=None, team_field_name=None, team_field_values=None, work_item_type_colors=None):
        super(TimelineTeamData, self).__init__()
        self.backlog = backlog
        self.field_reference_names = field_reference_names
        self.id = id
        self.is_expanded = is_expanded
        self.iterations = iterations
        self.name = name
        self.order_by_field = order_by_field
        self.partially_paged_field_reference_names = partially_paged_field_reference_names
        self.project_id = project_id
        self.status = status
        self.team_field_default_value = team_field_default_value
        self.team_field_name = team_field_name
        self.team_field_values = team_field_values
        self.work_item_type_colors = work_item_type_colors
