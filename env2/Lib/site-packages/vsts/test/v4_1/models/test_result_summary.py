# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultSummary(Model):
    """TestResultSummary.

    :param aggregated_results_analysis:
    :type aggregated_results_analysis: :class:`AggregatedResultsAnalysis <test.v4_1.models.AggregatedResultsAnalysis>`
    :param team_project:
    :type team_project: :class:`TeamProjectReference <test.v4_1.models.TeamProjectReference>`
    :param test_failures:
    :type test_failures: :class:`TestFailuresAnalysis <test.v4_1.models.TestFailuresAnalysis>`
    :param test_results_context:
    :type test_results_context: :class:`TestResultsContext <test.v4_1.models.TestResultsContext>`
    """

    _attribute_map = {
        'aggregated_results_analysis': {'key': 'aggregatedResultsAnalysis', 'type': 'AggregatedResultsAnalysis'},
        'team_project': {'key': 'teamProject', 'type': 'TeamProjectReference'},
        'test_failures': {'key': 'testFailures', 'type': 'TestFailuresAnalysis'},
        'test_results_context': {'key': 'testResultsContext', 'type': 'TestResultsContext'}
    }

    def __init__(self, aggregated_results_analysis=None, team_project=None, test_failures=None, test_results_context=None):
        super(TestResultSummary, self).__init__()
        self.aggregated_results_analysis = aggregated_results_analysis
        self.team_project = team_project
        self.test_failures = test_failures
        self.test_results_context = test_results_context
