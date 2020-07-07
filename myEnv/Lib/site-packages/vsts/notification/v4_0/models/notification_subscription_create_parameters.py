# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationSubscriptionCreateParameters(Model):
    """NotificationSubscriptionCreateParameters.

    :param channel: Channel for delivering notifications triggered by the new subscription.
    :type channel: :class:`ISubscriptionChannel <notification.v4_0.models.ISubscriptionChannel>`
    :param description: Brief description for the new subscription. Typically describes filter criteria which helps identity the subscription.
    :type description: str
    :param filter: Matching criteria for the new subscription. ExpressionFilter
    :type filter: :class:`ISubscriptionFilter <notification.v4_0.models.ISubscriptionFilter>`
    :param scope: The container in which events must be published from in order to be matched by the new subscription. If not specified, defaults to the current host (typically an account or project collection). For example, a subscription scoped to project A will not produce notifications for events published from project B.
    :type scope: :class:`SubscriptionScope <notification.v4_0.models.SubscriptionScope>`
    :param subscriber: User or group that will receive notifications for events matching the subscription's filter criteria. If not specified, defaults to the calling user.
    :type subscriber: :class:`IdentityRef <notification.v4_0.models.IdentityRef>`
    """

    _attribute_map = {
        'channel': {'key': 'channel', 'type': 'ISubscriptionChannel'},
        'description': {'key': 'description', 'type': 'str'},
        'filter': {'key': 'filter', 'type': 'ISubscriptionFilter'},
        'scope': {'key': 'scope', 'type': 'SubscriptionScope'},
        'subscriber': {'key': 'subscriber', 'type': 'IdentityRef'}
    }

    def __init__(self, channel=None, description=None, filter=None, scope=None, subscriber=None):
        super(NotificationSubscriptionCreateParameters, self).__init__()
        self.channel = channel
        self.description = description
        self.filter = filter
        self.scope = scope
        self.subscriber = subscriber
