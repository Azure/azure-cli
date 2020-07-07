# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultHistoryDetailsForGroup(Model):
    """TestResultHistoryDetailsForGroup.

    :param group_by_value:
    :type group_by_value: object
    :param latest_result:
    :type latest_result: :class:`TestCaseResult <test.v4_1.models.TestCaseResult>`
    """

    _attribute_map = {
        'group_by_value': {'key': 'groupByValue', 'type': 'object'},
        'latest_result': {'key': 'latestResult', 'type': 'TestCaseResult'}
    }

    def __init__(self, group_by_value=None, latest_result=None):
        super(TestResultHistoryDetailsForGroup, self).__init__()
        self.group_by_value = group_by_value
        self.latest_result = latest_result
