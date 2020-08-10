# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionEvaluationRequest(Model):
    """SubscriptionEvaluationRequest.

    :param min_events_created_date: The min created date for the events used for matching in UTC. Use all events created since this date
    :type min_events_created_date: datetime
    :param subscription_create_parameters: User or group that will receive notifications for events matching the subscription's filter criteria. If not specified, defaults to the calling user.
    :type subscription_create_parameters: :class:`NotificationSubscriptionCreateParameters <notification.v4_0.models.NotificationSubscriptionCreateParameters>`
    """

    _attribute_map = {
        'min_events_created_date': {'key': 'minEventsCreatedDate', 'type': 'iso-8601'},
        'subscription_create_parameters': {'key': 'subscriptionCreateParameters', 'type': 'NotificationSubscriptionCreateParameters'}
    }

    def __init__(self, min_events_created_date=None, subscription_create_parameters=None):
        super(SubscriptionEvaluationRequest, self).__init__()
        self.min_events_created_date = min_events_created_date
        self.subscription_create_parameters = subscription_create_parameters
