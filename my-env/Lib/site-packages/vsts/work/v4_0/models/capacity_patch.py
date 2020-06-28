# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CapacityPatch(Model):
    """CapacityPatch.

    :param activities:
    :type activities: list of :class:`Activity <work.v4_0.models.Activity>`
    :param days_off:
    :type days_off: list of :class:`DateRange <work.v4_0.models.DateRange>`
    """

    _attribute_map = {
        'activities': {'key': 'activities', 'type': '[Activity]'},
        'days_off': {'key': 'daysOff', 'type': '[DateRange]'}
    }

    def __init__(self, activities=None, days_off=None):
        super(CapacityPatch, self).__init__()
        self.activities = activities
        self.days_off = days_off
