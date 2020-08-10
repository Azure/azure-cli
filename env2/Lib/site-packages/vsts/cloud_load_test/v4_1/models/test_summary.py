# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestSummary(Model):
    """TestSummary.

    :param average_test_time:
    :type average_test_time: float
    :param failed_tests:
    :type failed_tests: int
    :param passed_tests:
    :type passed_tests: int
    :param percentile_data:
    :type percentile_data: list of :class:`SummaryPercentileData <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.SummaryPercentileData>`
    :param scenario_name:
    :type scenario_name: str
    :param test_name:
    :type test_name: str
    :param total_tests:
    :type total_tests: int
    """

    _attribute_map = {
        'average_test_time': {'key': 'averageTestTime', 'type': 'float'},
        'failed_tests': {'key': 'failedTests', 'type': 'int'},
        'passed_tests': {'key': 'passedTests', 'type': 'int'},
        'percentile_data': {'key': 'percentileData', 'type': '[SummaryPercentileData]'},
        'scenario_name': {'key': 'scenarioName', 'type': 'str'},
        'test_name': {'key': 'testName', 'type': 'str'},
        'total_tests': {'key': 'totalTests', 'type': 'int'}
    }

    def __init__(self, average_test_time=None, failed_tests=None, passed_tests=None, percentile_data=None, scenario_name=None, test_name=None, total_tests=None):
        super(TestSummary, self).__init__()
        self.average_test_time = average_test_time
        self.failed_tests = failed_tests
        self.passed_tests = passed_tests
        self.percentile_data = percentile_data
        self.scenario_name = scenario_name
        self.test_name = test_name
        self.total_tests = total_tests
