# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CounterSamplesResult(Model):
    """CounterSamplesResult.

    :param count:
    :type count: int
    :param max_batch_size:
    :type max_batch_size: int
    :param total_samples_count:
    :type total_samples_count: int
    :param values:
    :type values: list of :class:`CounterInstanceSamples <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.CounterInstanceSamples>`
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'max_batch_size': {'key': 'maxBatchSize', 'type': 'int'},
        'total_samples_count': {'key': 'totalSamplesCount', 'type': 'int'},
        'values': {'key': 'values', 'type': '[CounterInstanceSamples]'}
    }

    def __init__(self, count=None, max_batch_size=None, total_samples_count=None, values=None):
        super(CounterSamplesResult, self).__init__()
        self.count = count
        self.max_batch_size = max_batch_size
        self.total_samples_count = total_samples_count
        self.values = values
