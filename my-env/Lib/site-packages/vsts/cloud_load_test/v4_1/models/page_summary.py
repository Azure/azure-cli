# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PageSummary(Model):
    """PageSummary.

    :param average_page_time:
    :type average_page_time: float
    :param page_url:
    :type page_url: str
    :param percentage_pages_meeting_goal:
    :type percentage_pages_meeting_goal: int
    :param percentile_data:
    :type percentile_data: list of :class:`SummaryPercentileData <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.SummaryPercentileData>`
    :param scenario_name:
    :type scenario_name: str
    :param test_name:
    :type test_name: str
    :param total_pages:
    :type total_pages: int
    """

    _attribute_map = {
        'average_page_time': {'key': 'averagePageTime', 'type': 'float'},
        'page_url': {'key': 'pageUrl', 'type': 'str'},
        'percentage_pages_meeting_goal': {'key': 'percentagePagesMeetingGoal', 'type': 'int'},
        'percentile_data': {'key': 'percentileData', 'type': '[SummaryPercentileData]'},
        'scenario_name': {'key': 'scenarioName', 'type': 'str'},
        'test_name': {'key': 'testName', 'type': 'str'},
        'total_pages': {'key': 'totalPages', 'type': 'int'}
    }

    def __init__(self, average_page_time=None, page_url=None, percentage_pages_meeting_goal=None, percentile_data=None, scenario_name=None, test_name=None, total_pages=None):
        super(PageSummary, self).__init__()
        self.average_page_time = average_page_time
        self.page_url = page_url
        self.percentage_pages_meeting_goal = percentage_pages_meeting_goal
        self.percentile_data = percentile_data
        self.scenario_name = scenario_name
        self.test_name = test_name
        self.total_pages = total_pages
