# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationSubscriptionTemplate(Model):
    """NotificationSubscriptionTemplate.

    :param description:
    :type description: str
    :param filter:
    :type filter: :class:`ISubscriptionFilter <notification.v4_1.models.ISubscriptionFilter>`
    :param id:
    :type id: str
    :param notification_event_information:
    :type notification_event_information: :class:`NotificationEventType <notification.v4_1.models.NotificationEventType>`
    :param type:
    :type type: object
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'filter': {'key': 'filter', 'type': 'ISubscriptionFilter'},
        'id': {'key': 'id', 'type': 'str'},
        'notification_event_information': {'key': 'notificationEventInformation', 'type': 'NotificationEventType'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, description=None, filter=None, id=None, notification_event_information=None, type=None):
        super(NotificationSubscriptionTemplate, self).__init__()
        self.description = description
        self.filter = filter
        self.id = id
        self.notification_event_information = notification_event_information
        self.type = type
