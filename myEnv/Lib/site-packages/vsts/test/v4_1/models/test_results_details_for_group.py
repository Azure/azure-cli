# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultsDetailsForGroup(Model):
    """TestResultsDetailsForGroup.

    :param group_by_value:
    :type group_by_value: object
    :param results:
    :type results: list of :class:`TestCaseResult <test.v4_1.models.TestCaseResult>`
    :param results_count_by_outcome:
    :type results_count_by_outcome: dict
    """

    _attribute_map = {
        'group_by_value': {'key': 'groupByValue', 'type': 'object'},
        'results': {'key': 'results', 'type': '[TestCaseResult]'},
        'results_count_by_outcome': {'key': 'resultsCountByOutcome', 'type': '{AggregatedResultsByOutcome}'}
    }

    def __init__(self, group_by_value=None, results=None, results_count_by_outcome=None):
        super(TestResultsDetailsForGroup, self).__init__()
        self.group_by_value = group_by_value
        self.results = results
        self.results_count_by_outcome = results_count_by_outcome
