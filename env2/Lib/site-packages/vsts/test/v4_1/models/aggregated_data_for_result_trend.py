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
    :param run_summary_by_state:
    :type run_summary_by_state: dict
    :param test_results_context:
    :type test_results_context: :class:`TestResultsContext <test.v4_1.models.TestResultsContext>`
    :param total_tests:
    :type total_tests: int
    """

    _attribute_map = {
        'duration': {'key': 'duration', 'type': 'object'},
        'results_by_outcome': {'key': 'resultsByOutcome', 'type': '{AggregatedResultsByOutcome}'},
        'run_summary_by_state': {'key': 'runSummaryByState', 'type': '{AggregatedRunsByState}'},
        'test_results_context': {'key': 'testResultsContext', 'type': 'TestResultsContext'},
        'total_tests': {'key': 'totalTests', 'type': 'int'}
    }

    def __init__(self, duration=None, results_by_outcome=None, run_summary_by_state=None, test_results_context=None, total_tests=None):
        super(AggregatedDataForResultTrend, self).__init__()
        self.duration = duration
        self.results_by_outcome = results_by_outcome
        self.run_summary_by_state = run_summary_by_state
        self.test_results_context = test_results_context
        self.total_tests = total_tests
