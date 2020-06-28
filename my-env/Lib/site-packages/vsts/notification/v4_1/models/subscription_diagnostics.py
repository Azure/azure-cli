# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionDiagnostics(Model):
    """SubscriptionDiagnostics.

    :param delivery_results:
    :type delivery_results: :class:`SubscriptionTracing <notification.v4_1.models.SubscriptionTracing>`
    :param delivery_tracing:
    :type delivery_tracing: :class:`SubscriptionTracing <notification.v4_1.models.SubscriptionTracing>`
    :param evaluation_tracing:
    :type evaluation_tracing: :class:`SubscriptionTracing <notification.v4_1.models.SubscriptionTracing>`
    """

    _attribute_map = {
        'delivery_results': {'key': 'deliveryResults', 'type': 'SubscriptionTracing'},
        'delivery_tracing': {'key': 'deliveryTracing', 'type': 'SubscriptionTracing'},
        'evaluation_tracing': {'key': 'evaluationTracing', 'type': 'SubscriptionTracing'}
    }

    def __init__(self, delivery_results=None, delivery_tracing=None, evaluation_tracing=None):
        super(SubscriptionDiagnostics, self).__init__()
        self.delivery_results = delivery_results
        self.delivery_tracing = delivery_tracing
        self.evaluation_tracing = evaluation_tracing
