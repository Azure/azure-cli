# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionTracing(Model):
    """SubscriptionTracing.

    :param enabled:
    :type enabled: bool
    :param end_date: Trace until the specified end date.
    :type end_date: datetime
    :param max_traced_entries: The maximum number of result details to trace.
    :type max_traced_entries: int
    :param start_date: The date and time tracing started.
    :type start_date: datetime
    :param traced_entries: Trace until remaining count reaches 0.
    :type traced_entries: int
    """

    _attribute_map = {
        'enabled': {'key': 'enabled', 'type': 'bool'},
        'end_date': {'key': 'endDate', 'type': 'iso-8601'},
        'max_traced_entries': {'key': 'maxTracedEntries', 'type': 'int'},
        'start_date': {'key': 'startDate', 'type': 'iso-8601'},
        'traced_entries': {'key': 'tracedEntries', 'type': 'int'}
    }

    def __init__(self, enabled=None, end_date=None, max_traced_entries=None, start_date=None, traced_entries=None):
        super(SubscriptionTracing, self).__init__()
        self.enabled = enabled
        self.end_date = end_date
        self.max_traced_entries = max_traced_entries
        self.start_date = start_date
        self.traced_entries = traced_entries
