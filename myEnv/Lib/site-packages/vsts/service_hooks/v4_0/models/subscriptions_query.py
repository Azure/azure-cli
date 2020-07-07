# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionsQuery(Model):
    """SubscriptionsQuery.

    :param consumer_action_id: Optional consumer action id to restrict the results to (null for any)
    :type consumer_action_id: str
    :param consumer_id: Optional consumer id to restrict the results to (null for any)
    :type consumer_id: str
    :param consumer_input_filters: Filter for subscription consumer inputs
    :type consumer_input_filters: list of :class:`InputFilter <service-hooks.v4_0.models.InputFilter>`
    :param event_type: Optional event type id to restrict the results to (null for any)
    :type event_type: str
    :param publisher_id: Optional publisher id to restrict the results to (null for any)
    :type publisher_id: str
    :param publisher_input_filters: Filter for subscription publisher inputs
    :type publisher_input_filters: list of :class:`InputFilter <service-hooks.v4_0.models.InputFilter>`
    :param results: Results from the query
    :type results: list of :class:`Subscription <service-hooks.v4_0.models.Subscription>`
    :param subscriber_id: Optional subscriber filter.
    :type subscriber_id: str
    """

    _attribute_map = {
        'consumer_action_id': {'key': 'consumerActionId', 'type': 'str'},
        'consumer_id': {'key': 'consumerId', 'type': 'str'},
        'consumer_input_filters': {'key': 'consumerInputFilters', 'type': '[InputFilter]'},
        'event_type': {'key': 'eventType', 'type': 'str'},
        'publisher_id': {'key': 'publisherId', 'type': 'str'},
        'publisher_input_filters': {'key': 'publisherInputFilters', 'type': '[InputFilter]'},
        'results': {'key': 'results', 'type': '[Subscription]'},
        'subscriber_id': {'key': 'subscriberId', 'type': 'str'}
    }

    def __init__(self, consumer_action_id=None, consumer_id=None, consumer_input_filters=None, event_type=None, publisher_id=None, publisher_input_filters=None, results=None, subscriber_id=None):
        super(SubscriptionsQuery, self).__init__()
        self.consumer_action_id = consumer_action_id
        self.consumer_id = consumer_id
        self.consumer_input_filters = consumer_input_filters
        self.event_type = event_type
        self.publisher_id = publisher_id
        self.publisher_input_filters = publisher_input_filters
        self.results = results
        self.subscriber_id = subscriber_id
