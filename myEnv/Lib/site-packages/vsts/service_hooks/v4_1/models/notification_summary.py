# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationSummary(Model):
    """NotificationSummary.

    :param results: The notification results for this particular subscription.
    :type results: list of :class:`NotificationResultsSummaryDetail <service-hooks.v4_1.models.NotificationResultsSummaryDetail>`
    :param subscription_id: The subscription id associated with this notification
    :type subscription_id: str
    """

    _attribute_map = {
        'results': {'key': 'results', 'type': '[NotificationResultsSummaryDetail]'},
        'subscription_id': {'key': 'subscriptionId', 'type': 'str'}
    }

    def __init__(self, results=None, subscription_id=None):
        super(NotificationSummary, self).__init__()
        self.results = results
        self.subscription_id = subscription_id
