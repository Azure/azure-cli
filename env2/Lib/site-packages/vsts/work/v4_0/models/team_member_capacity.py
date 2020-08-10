# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .team_settings_data_contract_base import TeamSettingsDataContractBase


class TeamMemberCapacity(TeamSettingsDataContractBase):
    """TeamMemberCapacity.

    :param _links: Collection of links relevant to resource
    :type _links: :class:`ReferenceLinks <work.v4_0.models.ReferenceLinks>`
    :param url: Full http link to the resource
    :type url: str
    :param activities: Collection of capacities associated with the team member
    :type activities: list of :class:`Activity <work.v4_0.models.Activity>`
    :param days_off: The days off associated with the team member
    :type days_off: list of :class:`DateRange <work.v4_0.models.DateRange>`
    :param team_member: Shallow Ref to the associated team member
    :type team_member: :class:`Member <work.v4_0.models.Member>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'url': {'key': 'url', 'type': 'str'},
        'activities': {'key': 'activities', 'type': '[Activity]'},
        'days_off': {'key': 'daysOff', 'type': '[DateRange]'},
        'team_member': {'key': 'teamMember', 'type': 'Member'}
    }

    def __init__(self, _links=None, url=None, activities=None, days_off=None, team_member=None):
        super(TeamMemberCapacity, self).__init__(_links=_links, url=url)
        self.activities = activities
        self.days_off = days_off
        self.team_member = team_member
