# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CounterSample(Model):
    """CounterSample.

    :param base_value:
    :type base_value: long
    :param computed_value:
    :type computed_value: int
    :param counter_frequency:
    :type counter_frequency: long
    :param counter_instance_id:
    :type counter_instance_id: str
    :param counter_type:
    :type counter_type: str
    :param interval_end_date:
    :type interval_end_date: datetime
    :param interval_number:
    :type interval_number: int
    :param raw_value:
    :type raw_value: long
    :param system_frequency:
    :type system_frequency: long
    :param time_stamp:
    :type time_stamp: long
    """

    _attribute_map = {
        'base_value': {'key': 'baseValue', 'type': 'long'},
        'computed_value': {'key': 'computedValue', 'type': 'int'},
        'counter_frequency': {'key': 'counterFrequency', 'type': 'long'},
        'counter_instance_id': {'key': 'counterInstanceId', 'type': 'str'},
        'counter_type': {'key': 'counterType', 'type': 'str'},
        'interval_end_date': {'key': 'intervalEndDate', 'type': 'iso-8601'},
        'interval_number': {'key': 'intervalNumber', 'type': 'int'},
        'raw_value': {'key': 'rawValue', 'type': 'long'},
        'system_frequency': {'key': 'systemFrequency', 'type': 'long'},
        'time_stamp': {'key': 'timeStamp', 'type': 'long'}
    }

    def __init__(self, base_value=None, computed_value=None, counter_frequency=None, counter_instance_id=None, counter_type=None, interval_end_date=None, interval_number=None, raw_value=None, system_frequency=None, time_stamp=None):
        super(CounterSample, self).__init__()
        self.base_value = base_value
        self.computed_value = computed_value
        self.counter_frequency = counter_frequency
        self.counter_instance_id = counter_instance_id
        self.counter_type = counter_type
        self.interval_end_date = interval_end_date
        self.interval_number = interval_number
        self.raw_value = raw_value
        self.system_frequency = system_frequency
        self.time_stamp = time_stamp
