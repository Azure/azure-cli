# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BatchNotificationOperation(Model):
    """BatchNotificationOperation.

    :param notification_operation:
    :type notification_operation: object
    :param notification_query_conditions:
    :type notification_query_conditions: list of :class:`NotificationQueryCondition <notification.v4_0.models.NotificationQueryCondition>`
    """

    _attribute_map = {
        'notification_operation': {'key': 'notificationOperation', 'type': 'object'},
        'notification_query_conditions': {'key': 'notificationQueryConditions', 'type': '[NotificationQueryCondition]'}
    }

    def __init__(self, notification_operation=None, notification_query_conditions=None):
        super(BatchNotificationOperation, self).__init__()
        self.notification_operation = notification_operation
        self.notification_query_conditions = notification_query_conditions
