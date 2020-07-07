# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LinkedWorkItemsQuery(Model):
    """LinkedWorkItemsQuery.

    :param automated_test_names:
    :type automated_test_names: list of str
    :param plan_id:
    :type plan_id: int
    :param point_ids:
    :type point_ids: list of int
    :param suite_ids:
    :type suite_ids: list of int
    :param test_case_ids:
    :type test_case_ids: list of int
    :param work_item_category:
    :type work_item_category: str
    """

    _attribute_map = {
        'automated_test_names': {'key': 'automatedTestNames', 'type': '[str]'},
        'plan_id': {'key': 'planId', 'type': 'int'},
        'point_ids': {'key': 'pointIds', 'type': '[int]'},
        'suite_ids': {'key': 'suiteIds', 'type': '[int]'},
        'test_case_ids': {'key': 'testCaseIds', 'type': '[int]'},
        'work_item_category': {'key': 'workItemCategory', 'type': 'str'}
    }

    def __init__(self, automated_test_names=None, plan_id=None, point_ids=None, suite_ids=None, test_case_ids=None, work_item_category=None):
        super(LinkedWorkItemsQuery, self).__init__()
        self.automated_test_names = automated_test_names
        self.plan_id = plan_id
        self.point_ids = point_ids
        self.suite_ids = suite_ids
        self.test_case_ids = test_case_ids
        self.work_item_category = work_item_category
