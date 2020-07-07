# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ResultsFilter(Model):
    """ResultsFilter.

    :param automated_test_name:
    :type automated_test_name: str
    :param branch:
    :type branch: str
    :param group_by:
    :type group_by: str
    :param max_complete_date:
    :type max_complete_date: datetime
    :param results_count:
    :type results_count: int
    :param test_results_context:
    :type test_results_context: :class:`TestResultsContext <test.v4_0.models.TestResultsContext>`
    :param trend_days:
    :type trend_days: int
    """

    _attribute_map = {
        'automated_test_name': {'key': 'automatedTestName', 'type': 'str'},
        'branch': {'key': 'branch', 'type': 'str'},
        'group_by': {'key': 'groupBy', 'type': 'str'},
        'max_complete_date': {'key': 'maxCompleteDate', 'type': 'iso-8601'},
        'results_count': {'key': 'resultsCount', 'type': 'int'},
        'test_results_context': {'key': 'testResultsContext', 'type': 'TestResultsContext'},
        'trend_days': {'key': 'trendDays', 'type': 'int'}
    }

    def __init__(self, automated_test_name=None, branch=None, group_by=None, max_complete_date=None, results_count=None, test_results_context=None, trend_days=None):
        super(ResultsFilter, self).__init__()
        self.automated_test_name = automated_test_name
        self.branch = branch
        self.group_by = group_by
        self.max_complete_date = max_complete_date
        self.results_count = results_count
        self.test_results_context = test_results_context
        self.trend_days = trend_days
