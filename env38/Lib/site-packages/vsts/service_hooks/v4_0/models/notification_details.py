# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationDetails(Model):
    """NotificationDetails.

    :param completed_date: Gets or sets the time that this notification was completed (response received from the consumer)
    :type completed_date: datetime
    :param consumer_action_id: Gets or sets this notification detail's consumer action identifier.
    :type consumer_action_id: str
    :param consumer_id: Gets or sets this notification detail's consumer identifier.
    :type consumer_id: str
    :param consumer_inputs: Gets or sets this notification detail's consumer inputs.
    :type consumer_inputs: dict
    :param dequeued_date: Gets or sets the time that this notification was dequeued for processing
    :type dequeued_date: datetime
    :param error_detail: Gets or sets this notification detail's error detail.
    :type error_detail: str
    :param error_message: Gets or sets this notification detail's error message.
    :type error_message: str
    :param event: Gets or sets this notification detail's event content.
    :type event: :class:`Event <service-hooks.v4_0.models.Event>`
    :param event_type: Gets or sets this notification detail's event type.
    :type event_type: str
    :param processed_date: Gets or sets the time that this notification was finished processing (just before the request is sent to the consumer)
    :type processed_date: datetime
    :param publisher_id: Gets or sets this notification detail's publisher identifier.
    :type publisher_id: str
    :param publisher_inputs: Gets or sets this notification detail's publisher inputs.
    :type publisher_inputs: dict
    :param queued_date: Gets or sets the time that this notification was queued (created)
    :type queued_date: datetime
    :param request: Gets or sets this notification detail's request.
    :type request: str
    :param request_attempts: Number of requests attempted to be sent to the consumer
    :type request_attempts: int
    :param request_duration: Duration of the request to the consumer in seconds
    :type request_duration: float
    :param response: Gets or sets this notification detail's reponse.
    :type response: str
    """

    _attribute_map = {
        'completed_date': {'key': 'completedDate', 'type': 'iso-8601'},
        'consumer_action_id': {'key': 'consumerActionId', 'type': 'str'},
        'consumer_id': {'key': 'consumerId', 'type': 'str'},
        'consumer_inputs': {'key': 'consumerInputs', 'type': '{str}'},
        'dequeued_date': {'key': 'dequeuedDate', 'type': 'iso-8601'},
        'error_detail': {'key': 'errorDetail', 'type': 'str'},
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'event': {'key': 'event', 'type': 'Event'},
        'event_type': {'key': 'eventType', 'type': 'str'},
        'processed_date': {'key': 'processedDate', 'type': 'iso-8601'},
        'publisher_id': {'key': 'publisherId', 'type': 'str'},
        'publisher_inputs': {'key': 'publisherInputs', 'type': '{str}'},
        'queued_date': {'key': 'queuedDate', 'type': 'iso-8601'},
        'request': {'key': 'request', 'type': 'str'},
        'request_attempts': {'key': 'requestAttempts', 'type': 'int'},
        'request_duration': {'key': 'requestDuration', 'type': 'float'},
        'response': {'key': 'response', 'type': 'str'}
    }

    def __init__(self, completed_date=None, consumer_action_id=None, consumer_id=None, consumer_inputs=None, dequeued_date=None, error_detail=None, error_message=None, event=None, event_type=None, processed_date=None, publisher_id=None, publisher_inputs=None, queued_date=None, request=None, request_attempts=None, request_duration=None, response=None):
        super(NotificationDetails, self).__init__()
        self.completed_date = completed_date
        self.consumer_action_id = consumer_action_id
        self.consumer_id = consumer_id
        self.consumer_inputs = consumer_inputs
        self.dequeued_date = dequeued_date
        self.error_detail = error_detail
        self.error_message = error_message
        self.event = event
        self.event_type = event_type
        self.processed_date = processed_date
        self.publisher_id = publisher_id
        self.publisher_inputs = publisher_inputs
        self.queued_date = queued_date
        self.request = request
        self.request_attempts = request_attempts
        self.request_duration = request_duration
        self.response = response
