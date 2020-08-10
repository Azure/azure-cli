# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .team_settings_data_contract_base import TeamSettingsDataContractBase


class TeamSettingsDaysOff(TeamSettingsDataContractBase):
    """TeamSettingsDaysOff.

    :param _links: Collection of links relevant to resource
    :type _links: :class:`ReferenceLinks <work.v4_1.models.ReferenceLinks>`
    :param url: Full http link to the resource
    :type url: str
    :param days_off:
    :type days_off: list of :class:`DateRange <work.v4_1.models.DateRange>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'url': {'key': 'url', 'type': 'str'},
        'days_off': {'key': 'daysOff', 'type': '[DateRange]'}
    }

    def __init__(self, _links=None, url=None, days_off=None):
        super(TeamSettingsDaysOff, self).__init__(_links=_links, url=url)
        self.days_off = days_off
