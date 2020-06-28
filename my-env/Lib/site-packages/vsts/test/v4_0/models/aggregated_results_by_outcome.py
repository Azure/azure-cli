# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AggregatedResultsByOutcome(Model):
    """AggregatedResultsByOutcome.

    :param count:
    :type count: int
    :param duration:
    :type duration: object
    :param group_by_field:
    :type group_by_field: str
    :param group_by_value:
    :type group_by_value: object
    :param outcome:
    :type outcome: object
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'duration': {'key': 'duration', 'type': 'object'},
        'group_by_field': {'key': 'groupByField', 'type': 'str'},
        'group_by_value': {'key': 'groupByValue', 'type': 'object'},
        'outcome': {'key': 'outcome', 'type': 'object'}
    }

    def __init__(self, count=None, duration=None, group_by_field=None, group_by_value=None, outcome=None):
        super(AggregatedResultsByOutcome, self).__init__()
        self.count = count
        self.duration = duration
        self.group_by_field = group_by_field
        self.group_by_value = group_by_value
        self.outcome = outcome
