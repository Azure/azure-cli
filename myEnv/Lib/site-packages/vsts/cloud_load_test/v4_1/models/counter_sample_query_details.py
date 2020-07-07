# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CounterSampleQueryDetails(Model):
    """CounterSampleQueryDetails.

    :param counter_instance_id:
    :type counter_instance_id: str
    :param from_interval:
    :type from_interval: int
    :param to_interval:
    :type to_interval: int
    """

    _attribute_map = {
        'counter_instance_id': {'key': 'counterInstanceId', 'type': 'str'},
        'from_interval': {'key': 'fromInterval', 'type': 'int'},
        'to_interval': {'key': 'toInterval', 'type': 'int'}
    }

    def __init__(self, counter_instance_id=None, from_interval=None, to_interval=None):
        super(CounterSampleQueryDetails, self).__init__()
        self.counter_instance_id = counter_instance_id
        self.from_interval = from_interval
        self.to_interval = to_interval
