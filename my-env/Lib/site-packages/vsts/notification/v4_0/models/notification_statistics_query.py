# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationStatisticsQuery(Model):
    """NotificationStatisticsQuery.

    :param conditions:
    :type conditions: list of :class:`NotificationStatisticsQueryConditions <notification.v4_0.models.NotificationStatisticsQueryConditions>`
    """

    _attribute_map = {
        'conditions': {'key': 'conditions', 'type': '[NotificationStatisticsQueryConditions]'}
    }

    def __init__(self, conditions=None):
        super(NotificationStatisticsQuery, self).__init__()
        self.conditions = conditions
