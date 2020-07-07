# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AggregatedDataForResultTrend(Model):
    """AggregatedDataForResultTrend.

    :param duration: This is tests execution duration.
    :type duration: object
    :param results_by_outcome:
    :type results_by_outcome: dict
    :param test_results_context:
    :type test_results_context: :class:`TestResultsContext <test.v4_0.models.TestResultsContext>`
    :param total_tests:
    :type total_tests: int
    """

    _attribute_map = {
        'duration': {'key': 'duration', 'type': 'object'},
        'results_by_outcome': {'key': 'resultsByOutcome', 'type': '{AggregatedResultsByOutcome}'},
        'test_results_context': {'key': 'testResultsContext', 'type': 'TestResultsContext'},
        'total_tests': {'key': 'totalTests', 'type': 'int'}
    }

    def __init__(self, duration=None, results_by_outcome=None, test_results_context=None, total_tests=None):
        super(AggregatedDataForResultTrend, self).__init__()
        self.duration = duration
        self.results_by_outcome = results_by_outcome
        self.test_results_context = test_results_context
        self.total_tests = total_tests
