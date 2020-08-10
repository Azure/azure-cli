# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Notification(Model):
    """Notification.

    :param created_date: Gets or sets date and time that this result was created.
    :type created_date: datetime
    :param details: Details about this notification (if available)
    :type details: :class:`NotificationDetails <service-hooks.v4_0.models.NotificationDetails>`
    :param event_id: The event id associated with this notification
    :type event_id: str
    :param id: The notification id
    :type id: int
    :param modified_date: Gets or sets date and time that this result was last modified.
    :type modified_date: datetime
    :param result: Result of the notification
    :type result: object
    :param status: Status of the notification
    :type status: object
    :param subscriber_id: The subscriber Id  associated with this notification. This is the last identity who touched in the subscription. In case of test notifications it can be the tester if the subscription is not created yet.
    :type subscriber_id: str
    :param subscription_id: The subscription id associated with this notification
    :type subscription_id: str
    """

    _attribute_map = {
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'details': {'key': 'details', 'type': 'NotificationDetails'},
        'event_id': {'key': 'eventId', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'modified_date': {'key': 'modifiedDate', 'type': 'iso-8601'},
        'result': {'key': 'result', 'type': 'object'},
        'status': {'key': 'status', 'type': 'object'},
        'subscriber_id': {'key': 'subscriberId', 'type': 'str'},
        'subscription_id': {'key': 'subscriptionId', 'type': 'str'}
    }

    def __init__(self, created_date=None, details=None, event_id=None, id=None, modified_date=None, result=None, status=None, subscriber_id=None, subscription_id=None):
        super(Notification, self).__init__()
        self.created_date = created_date
        self.details = details
        self.event_id = event_id
        self.id = id
        self.modified_date = modified_date
        self.result = result
        self.status = status
        self.subscriber_id = subscriber_id
        self.subscription_id = subscription_id
