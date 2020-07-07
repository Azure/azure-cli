# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationEventPublisher(Model):
    """NotificationEventPublisher.

    :param id:
    :type id: str
    :param subscription_management_info:
    :type subscription_management_info: :class:`SubscriptionManagement <notification.v4_1.models.SubscriptionManagement>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'subscription_management_info': {'key': 'subscriptionManagementInfo', 'type': 'SubscriptionManagement'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, id=None, subscription_management_info=None, url=None):
        super(NotificationEventPublisher, self).__init__()
        self.id = id
        self.subscription_management_info = subscription_management_info
        self.url = url
