# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Activity(Model):
    """Activity.

    :param capacity_per_day:
    :type capacity_per_day: int
    :param name:
    :type name: str
    """

    _attribute_map = {
        'capacity_per_day': {'key': 'capacityPerDay', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, capacity_per_day=None, name=None):
        super(Activity, self).__init__()
        self.capacity_per_day = capacity_per_day
        self.name = name
