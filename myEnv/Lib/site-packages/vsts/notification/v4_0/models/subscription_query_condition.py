# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionQueryCondition(Model):
    """SubscriptionQueryCondition.

    :param filter: Filter conditions that matching subscriptions must have. Typically only the filter's type and event type are used for matching.
    :type filter: :class:`ISubscriptionFilter <notification.v4_0.models.ISubscriptionFilter>`
    :param flags: Flags to specify the the type subscriptions to query for.
    :type flags: object
    :param scope: Scope that matching subscriptions must have.
    :type scope: str
    :param subscriber_id: ID of the subscriber (user or group) that matching subscriptions must be subscribed to.
    :type subscriber_id: str
    :param subscription_id: ID of the subscription to query for.
    :type subscription_id: str
    """

    _attribute_map = {
        'filter': {'key': 'filter', 'type': 'ISubscriptionFilter'},
        'flags': {'key': 'flags', 'type': 'object'},
        'scope': {'key': 'scope', 'type': 'str'},
        'subscriber_id': {'key': 'subscriberId', 'type': 'str'},
        'subscription_id': {'key': 'subscriptionId', 'type': 'str'}
    }

    def __init__(self, filter=None, flags=None, scope=None, subscriber_id=None, subscription_id=None):
        super(SubscriptionQueryCondition, self).__init__()
        self.filter = filter
        self.flags = flags
        self.scope = scope
        self.subscriber_id = subscriber_id
        self.subscription_id = subscription_id
