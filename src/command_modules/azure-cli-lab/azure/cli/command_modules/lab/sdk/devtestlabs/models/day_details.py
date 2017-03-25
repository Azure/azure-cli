# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class DayDetails(Model):
    """Properties of a daily schedule.

    :param time: The time of day the schedule will occur.
    :type time: str
    """

    _attribute_map = {
        'time': {'key': 'time', 'type': 'str'},
    }

    def __init__(self, time=None):
        self.time = time
