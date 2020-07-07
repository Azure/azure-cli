# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AggregatedResultsAnalysis(Model):
    """AggregatedResultsAnalysis.

    :param duration:
    :type duration: object
    :param not_reported_results_by_outcome:
    :type not_reported_results_by_outcome: dict
    :param previous_context:
    :type previous_context: :class:`TestResultsContext <test.v4_0.models.TestResultsContext>`
    :param results_by_outcome:
    :type results_by_outcome: dict
    :param results_difference:
    :type results_difference: :class:`AggregatedResultsDifference <test.v4_0.models.AggregatedResultsDifference>`
    :param total_tests:
    :type total_tests: int
    """

    _attribute_map = {
        'duration': {'key': 'duration', 'type': 'object'},
        'not_reported_results_by_outcome': {'key': 'notReportedResultsByOutcome', 'type': '{AggregatedResultsByOutcome}'},
        'previous_context': {'key': 'previousContext', 'type': 'TestResultsContext'},
        'results_by_outcome': {'key': 'resultsByOutcome', 'type': '{AggregatedResultsByOutcome}'},
        'results_difference': {'key': 'resultsDifference', 'type': 'AggregatedResultsDifference'},
        'total_tests': {'key': 'totalTests', 'type': 'int'}
    }

    def __init__(self, duration=None, not_reported_results_by_outcome=None, previous_context=None, results_by_outcome=None, results_difference=None, total_tests=None):
        super(AggregatedResultsAnalysis, self).__init__()
        self.duration = duration
        self.not_reported_results_by_outcome = not_reported_results_by_outcome
        self.previous_context = previous_context
        self.results_by_outcome = results_by_outcome
        self.results_difference = results_difference
        self.total_tests = total_tests
