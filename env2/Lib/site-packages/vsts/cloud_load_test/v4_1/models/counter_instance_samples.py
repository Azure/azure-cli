# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CounterInstanceSamples(Model):
    """CounterInstanceSamples.

    :param count:
    :type count: int
    :param counter_instance_id:
    :type counter_instance_id: str
    :param next_refresh_time:
    :type next_refresh_time: datetime
    :param values:
    :type values: list of :class:`CounterSample <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.CounterSample>`
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'counter_instance_id': {'key': 'counterInstanceId', 'type': 'str'},
        'next_refresh_time': {'key': 'nextRefreshTime', 'type': 'iso-8601'},
        'values': {'key': 'values', 'type': '[CounterSample]'}
    }

    def __init__(self, count=None, counter_instance_id=None, next_refresh_time=None, values=None):
        super(CounterInstanceSamples, self).__init__()
        self.count = count
        self.counter_instance_id = counter_instance_id
        self.next_refresh_time = next_refresh_time
        self.values = values
