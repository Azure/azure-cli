# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionEvaluationResult(Model):
    """SubscriptionEvaluationResult.

    :param evaluation_job_status: Subscription evaluation job status
    :type evaluation_job_status: object
    :param events: Subscription evaluation events results.
    :type events: :class:`EventsEvaluationResult <notification.v4_0.models.EventsEvaluationResult>`
    :param id: The requestId which is the subscription evaluation jobId
    :type id: str
    :param notifications: Subscription evaluation  notification results.
    :type notifications: :class:`NotificationsEvaluationResult <notification.v4_0.models.NotificationsEvaluationResult>`
    """

    _attribute_map = {
        'evaluation_job_status': {'key': 'evaluationJobStatus', 'type': 'object'},
        'events': {'key': 'events', 'type': 'EventsEvaluationResult'},
        'id': {'key': 'id', 'type': 'str'},
        'notifications': {'key': 'notifications', 'type': 'NotificationsEvaluationResult'}
    }

    def __init__(self, evaluation_job_status=None, events=None, id=None, notifications=None):
        super(SubscriptionEvaluationResult, self).__init__()
        self.evaluation_job_status = evaluation_job_status
        self.events = events
        self.id = id
        self.notifications = notifications
