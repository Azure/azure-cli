# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationSubscriptionUpdateParameters(Model):
    """NotificationSubscriptionUpdateParameters.

    :param admin_settings: Admin-managed settings for the subscription. Only applies to subscriptions where the subscriber is a group.
    :type admin_settings: :class:`SubscriptionAdminSettings <notification.v4_0.models.SubscriptionAdminSettings>`
    :param channel: Channel for delivering notifications triggered by the subscription.
    :type channel: :class:`ISubscriptionChannel <notification.v4_0.models.ISubscriptionChannel>`
    :param description: Updated description for the subscription. Typically describes filter criteria which helps identity the subscription.
    :type description: str
    :param filter: Matching criteria for the subscription. ExpressionFilter
    :type filter: :class:`ISubscriptionFilter <notification.v4_0.models.ISubscriptionFilter>`
    :param scope: The container in which events must be published from in order to be matched by the new subscription. If not specified, defaults to the current host (typically the current account or project collection). For example, a subscription scoped to project A will not produce notifications for events published from project B.
    :type scope: :class:`SubscriptionScope <notification.v4_0.models.SubscriptionScope>`
    :param status: Updated status for the subscription. Typically used to enable or disable a subscription.
    :type status: object
    :param status_message: Optional message that provides more details about the updated status.
    :type status_message: str
    :param user_settings: User-managed settings for the subscription. Only applies to subscriptions where the subscriber is a group. Typically used to opt-in or opt-out a user from a group subscription.
    :type user_settings: :class:`SubscriptionUserSettings <notification.v4_0.models.SubscriptionUserSettings>`
    """

    _attribute_map = {
        'admin_settings': {'key': 'adminSettings', 'type': 'SubscriptionAdminSettings'},
        'channel': {'key': 'channel', 'type': 'ISubscriptionChannel'},
        'description': {'key': 'description', 'type': 'str'},
        'filter': {'key': 'filter', 'type': 'ISubscriptionFilter'},
        'scope': {'key': 'scope', 'type': 'SubscriptionScope'},
        'status': {'key': 'status', 'type': 'object'},
        'status_message': {'key': 'statusMessage', 'type': 'str'},
        'user_settings': {'key': 'userSettings', 'type': 'SubscriptionUserSettings'}
    }

    def __init__(self, admin_settings=None, channel=None, description=None, filter=None, scope=None, status=None, status_message=None, user_settings=None):
        super(NotificationSubscriptionUpdateParameters, self).__init__()
        self.admin_settings = admin_settings
        self.channel = channel
        self.description = description
        self.filter = filter
        self.scope = scope
        self.status = status
        self.status_message = status_message
        self.user_settings = user_settings
