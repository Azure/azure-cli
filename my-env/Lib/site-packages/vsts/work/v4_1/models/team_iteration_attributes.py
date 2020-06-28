# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TeamIterationAttributes(Model):
    """TeamIterationAttributes.

    :param finish_date:
    :type finish_date: datetime
    :param start_date:
    :type start_date: datetime
    :param time_frame:
    :type time_frame: object
    """

    _attribute_map = {
        'finish_date': {'key': 'finishDate', 'type': 'iso-8601'},
        'start_date': {'key': 'startDate', 'type': 'iso-8601'},
        'time_frame': {'key': 'timeFrame', 'type': 'object'}
    }

    def __init__(self, finish_date=None, start_date=None, time_frame=None):
        super(TeamIterationAttributes, self).__init__()
        self.finish_date = finish_date
        self.start_date = start_date
        self.time_frame = time_frame
