# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationResultsSummaryDetail(Model):
    """NotificationResultsSummaryDetail.

    :param notification_count: Count of notification sent out with a matching result.
    :type notification_count: int
    :param result: Result of the notification
    :type result: object
    """

    _attribute_map = {
        'notification_count': {'key': 'notificationCount', 'type': 'int'},
        'result': {'key': 'result', 'type': 'object'}
    }

    def __init__(self, notification_count=None, result=None):
        super(NotificationResultsSummaryDetail, self).__init__()
        self.notification_count = notification_count
        self.result = result
