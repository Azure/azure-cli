# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationStatisticsQueryConditions(Model):
    """NotificationStatisticsQueryConditions.

    :param end_date:
    :type end_date: datetime
    :param hit_count_minimum:
    :type hit_count_minimum: int
    :param path:
    :type path: str
    :param start_date:
    :type start_date: datetime
    :param type:
    :type type: object
    :param user:
    :type user: :class:`IdentityRef <notification.v4_1.models.IdentityRef>`
    """

    _attribute_map = {
        'end_date': {'key': 'endDate', 'type': 'iso-8601'},
        'hit_count_minimum': {'key': 'hitCountMinimum', 'type': 'int'},
        'path': {'key': 'path', 'type': 'str'},
        'start_date': {'key': 'startDate', 'type': 'iso-8601'},
        'type': {'key': 'type', 'type': 'object'},
        'user': {'key': 'user', 'type': 'IdentityRef'}
    }

    def __init__(self, end_date=None, hit_count_minimum=None, path=None, start_date=None, type=None, user=None):
        super(NotificationStatisticsQueryConditions, self).__init__()
        self.end_date = end_date
        self.hit_count_minimum = hit_count_minimum
        self.path = path
        self.start_date = start_date
        self.type = type
        self.user = user
