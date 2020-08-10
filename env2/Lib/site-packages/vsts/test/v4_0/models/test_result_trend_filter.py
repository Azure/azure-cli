# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultTrendFilter(Model):
    """TestResultTrendFilter.

    :param branch_names:
    :type branch_names: list of str
    :param build_count:
    :type build_count: int
    :param definition_ids:
    :type definition_ids: list of int
    :param env_definition_ids:
    :type env_definition_ids: list of int
    :param max_complete_date:
    :type max_complete_date: datetime
    :param publish_context:
    :type publish_context: str
    :param test_run_titles:
    :type test_run_titles: list of str
    :param trend_days:
    :type trend_days: int
    """

    _attribute_map = {
        'branch_names': {'key': 'branchNames', 'type': '[str]'},
        'build_count': {'key': 'buildCount', 'type': 'int'},
        'definition_ids': {'key': 'definitionIds', 'type': '[int]'},
        'env_definition_ids': {'key': 'envDefinitionIds', 'type': '[int]'},
        'max_complete_date': {'key': 'maxCompleteDate', 'type': 'iso-8601'},
        'publish_context': {'key': 'publishContext', 'type': 'str'},
        'test_run_titles': {'key': 'testRunTitles', 'type': '[str]'},
        'trend_days': {'key': 'trendDays', 'type': 'int'}
    }

    def __init__(self, branch_names=None, build_count=None, definition_ids=None, env_definition_ids=None, max_complete_date=None, publish_context=None, test_run_titles=None, trend_days=None):
        super(TestResultTrendFilter, self).__init__()
        self.branch_names = branch_names
        self.build_count = build_count
        self.definition_ids = definition_ids
        self.env_definition_ids = env_definition_ids
        self.max_complete_date = max_complete_date
        self.publish_context = publish_context
        self.test_run_titles = test_run_titles
        self.trend_days = trend_days
