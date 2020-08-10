# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultHistory(Model):
    """TestResultHistory.

    :param group_by_field:
    :type group_by_field: str
    :param results_for_group:
    :type results_for_group: list of :class:`TestResultHistoryDetailsForGroup <test.v4_1.models.TestResultHistoryDetailsForGroup>`
    """

    _attribute_map = {
        'group_by_field': {'key': 'groupByField', 'type': 'str'},
        'results_for_group': {'key': 'resultsForGroup', 'type': '[TestResultHistoryDetailsForGroup]'}
    }

    def __init__(self, group_by_field=None, results_for_group=None):
        super(TestResultHistory, self).__init__()
        self.group_by_field = group_by_field
        self.results_for_group = results_for_group
