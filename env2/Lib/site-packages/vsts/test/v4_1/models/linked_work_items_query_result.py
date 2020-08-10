# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LinkedWorkItemsQueryResult(Model):
    """LinkedWorkItemsQueryResult.

    :param automated_test_name:
    :type automated_test_name: str
    :param plan_id:
    :type plan_id: int
    :param point_id:
    :type point_id: int
    :param suite_id:
    :type suite_id: int
    :param test_case_id:
    :type test_case_id: int
    :param work_items:
    :type work_items: list of :class:`WorkItemReference <test.v4_1.models.WorkItemReference>`
    """

    _attribute_map = {
        'automated_test_name': {'key': 'automatedTestName', 'type': 'str'},
        'plan_id': {'key': 'planId', 'type': 'int'},
        'point_id': {'key': 'pointId', 'type': 'int'},
        'suite_id': {'key': 'suiteId', 'type': 'int'},
        'test_case_id': {'key': 'testCaseId', 'type': 'int'},
        'work_items': {'key': 'workItems', 'type': '[WorkItemReference]'}
    }

    def __init__(self, automated_test_name=None, plan_id=None, point_id=None, suite_id=None, test_case_id=None, work_items=None):
        super(LinkedWorkItemsQueryResult, self).__init__()
        self.automated_test_name = automated_test_name
        self.plan_id = plan_id
        self.point_id = point_id
        self.suite_id = suite_id
        self.test_case_id = test_case_id
        self.work_items = work_items
