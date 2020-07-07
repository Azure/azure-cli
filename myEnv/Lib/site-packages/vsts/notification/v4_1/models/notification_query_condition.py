# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationQueryCondition(Model):
    """NotificationQueryCondition.

    :param event_initiator:
    :type event_initiator: str
    :param event_type:
    :type event_type: str
    :param subscriber:
    :type subscriber: str
    :param subscription_id:
    :type subscription_id: str
    """

    _attribute_map = {
        'event_initiator': {'key': 'eventInitiator', 'type': 'str'},
        'event_type': {'key': 'eventType', 'type': 'str'},
        'subscriber': {'key': 'subscriber', 'type': 'str'},
        'subscription_id': {'key': 'subscriptionId', 'type': 'str'}
    }

    def __init__(self, event_initiator=None, event_type=None, subscriber=None, subscription_id=None):
        super(NotificationQueryCondition, self).__init__()
        self.event_initiator = event_initiator
        self.event_type = event_type
        self.subscriber = subscriber
        self.subscription_id = subscription_id
