# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class EventsEvaluationResult(Model):
    """EventsEvaluationResult.

    :param count: Count of events evaluated.
    :type count: int
    :param matched_count: Count of matched events.
    :type matched_count: int
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'matched_count': {'key': 'matchedCount', 'type': 'int'}
    }

    def __init__(self, count=None, matched_count=None):
        super(EventsEvaluationResult, self).__init__()
        self.count = count
        self.matched_count = matched_count
