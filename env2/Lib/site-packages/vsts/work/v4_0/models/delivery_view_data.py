# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .plan_view_data import PlanViewData


class DeliveryViewData(PlanViewData):
    """DeliveryViewData.

    :param id:
    :type id: str
    :param revision:
    :type revision: int
    :param child_id_to_parent_id_map: Work item child id to parenet id map
    :type child_id_to_parent_id_map: dict
    :param criteria_status: Filter criteria status of the timeline
    :type criteria_status: :class:`TimelineCriteriaStatus <work.v4_0.models.TimelineCriteriaStatus>`
    :param end_date: The end date of the delivery view data
    :type end_date: datetime
    :param start_date: The start date for the delivery view data
    :type start_date: datetime
    :param teams: All the team data
    :type teams: list of :class:`TimelineTeamData <work.v4_0.models.TimelineTeamData>`
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'int'},
        'child_id_to_parent_id_map': {'key': 'childIdToParentIdMap', 'type': '{int}'},
        'criteria_status': {'key': 'criteriaStatus', 'type': 'TimelineCriteriaStatus'},
        'end_date': {'key': 'endDate', 'type': 'iso-8601'},
        'start_date': {'key': 'startDate', 'type': 'iso-8601'},
        'teams': {'key': 'teams', 'type': '[TimelineTeamData]'}
    }

    def __init__(self, id=None, revision=None, child_id_to_parent_id_map=None, criteria_status=None, end_date=None, start_date=None, teams=None):
        super(DeliveryViewData, self).__init__(id=id, revision=revision)
        self.child_id_to_parent_id_map = child_id_to_parent_id_map
        self.criteria_status = criteria_status
        self.end_date = end_date
        self.start_date = start_date
        self.teams = teams
