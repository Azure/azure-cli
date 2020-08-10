# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationStatistic(Model):
    """NotificationStatistic.

    :param date:
    :type date: datetime
    :param hit_count:
    :type hit_count: int
    :param path:
    :type path: str
    :param type:
    :type type: object
    :param user:
    :type user: :class:`IdentityRef <notification.v4_1.models.IdentityRef>`
    """

    _attribute_map = {
        'date': {'key': 'date', 'type': 'iso-8601'},
        'hit_count': {'key': 'hitCount', 'type': 'int'},
        'path': {'key': 'path', 'type': 'str'},
        'type': {'key': 'type', 'type': 'object'},
        'user': {'key': 'user', 'type': 'IdentityRef'}
    }

    def __init__(self, date=None, hit_count=None, path=None, type=None, user=None):
        super(NotificationStatistic, self).__init__()
        self.date = date
        self.hit_count = hit_count
        self.path = path
        self.type = type
        self.user = user
