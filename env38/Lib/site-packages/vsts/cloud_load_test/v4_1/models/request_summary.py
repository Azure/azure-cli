# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RequestSummary(Model):
    """RequestSummary.

    :param average_response_time:
    :type average_response_time: float
    :param failed_requests:
    :type failed_requests: int
    :param passed_requests:
    :type passed_requests: int
    :param percentile_data:
    :type percentile_data: list of :class:`SummaryPercentileData <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.SummaryPercentileData>`
    :param requests_per_sec:
    :type requests_per_sec: float
    :param request_url:
    :type request_url: str
    :param scenario_name:
    :type scenario_name: str
    :param test_name:
    :type test_name: str
    :param total_requests:
    :type total_requests: int
    """

    _attribute_map = {
        'average_response_time': {'key': 'averageResponseTime', 'type': 'float'},
        'failed_requests': {'key': 'failedRequests', 'type': 'int'},
        'passed_requests': {'key': 'passedRequests', 'type': 'int'},
        'percentile_data': {'key': 'percentileData', 'type': '[SummaryPercentileData]'},
        'requests_per_sec': {'key': 'requestsPerSec', 'type': 'float'},
        'request_url': {'key': 'requestUrl', 'type': 'str'},
        'scenario_name': {'key': 'scenarioName', 'type': 'str'},
        'test_name': {'key': 'testName', 'type': 'str'},
        'total_requests': {'key': 'totalRequests', 'type': 'int'}
    }

    def __init__(self, average_response_time=None, failed_requests=None, passed_requests=None, percentile_data=None, requests_per_sec=None, request_url=None, scenario_name=None, test_name=None, total_requests=None):
        super(RequestSummary, self).__init__()
        self.average_response_time = average_response_time
        self.failed_requests = failed_requests
        self.passed_requests = passed_requests
        self.percentile_data = percentile_data
        self.requests_per_sec = requests_per_sec
        self.request_url = request_url
        self.scenario_name = scenario_name
        self.test_name = test_name
        self.total_requests = total_requests
