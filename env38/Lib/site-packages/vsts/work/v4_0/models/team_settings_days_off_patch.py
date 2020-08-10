# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TeamSettingsDaysOffPatch(Model):
    """TeamSettingsDaysOffPatch.

    :param days_off:
    :type days_off: list of :class:`DateRange <work.v4_0.models.DateRange>`
    """

    _attribute_map = {
        'days_off': {'key': 'daysOff', 'type': '[DateRange]'}
    }

    def __init__(self, days_off=None):
        super(TeamSettingsDaysOffPatch, self).__init__()
        self.days_off = days_off
