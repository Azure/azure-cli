# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UpdateSubscripitonDiagnosticsParameters(Model):
    """UpdateSubscripitonDiagnosticsParameters.

    :param delivery_results:
    :type delivery_results: :class:`UpdateSubscripitonTracingParameters <microsoft.-visual-studio.-services.-notifications.-web-api.v4_1.models.UpdateSubscripitonTracingParameters>`
    :param delivery_tracing:
    :type delivery_tracing: :class:`UpdateSubscripitonTracingParameters <microsoft.-visual-studio.-services.-notifications.-web-api.v4_1.models.UpdateSubscripitonTracingParameters>`
    :param evaluation_tracing:
    :type evaluation_tracing: :class:`UpdateSubscripitonTracingParameters <microsoft.-visual-studio.-services.-notifications.-web-api.v4_1.models.UpdateSubscripitonTracingParameters>`
    """

    _attribute_map = {
        'delivery_results': {'key': 'deliveryResults', 'type': 'UpdateSubscripitonTracingParameters'},
        'delivery_tracing': {'key': 'deliveryTracing', 'type': 'UpdateSubscripitonTracingParameters'},
        'evaluation_tracing': {'key': 'evaluationTracing', 'type': 'UpdateSubscripitonTracingParameters'}
    }

    def __init__(self, delivery_results=None, delivery_tracing=None, evaluation_tracing=None):
        super(UpdateSubscripitonDiagnosticsParameters, self).__init__()
        self.delivery_results = delivery_results
        self.delivery_tracing = delivery_tracing
        self.evaluation_tracing = evaluation_tracing
