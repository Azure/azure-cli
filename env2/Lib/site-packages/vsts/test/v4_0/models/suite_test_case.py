# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SuiteTestCase(Model):
    """SuiteTestCase.

    :param point_assignments:
    :type point_assignments: list of :class:`PointAssignment <test.v4_0.models.PointAssignment>`
    :param test_case:
    :type test_case: :class:`WorkItemReference <test.v4_0.models.WorkItemReference>`
    """

    _attribute_map = {
        'point_assignments': {'key': 'pointAssignments', 'type': '[PointAssignment]'},
        'test_case': {'key': 'testCase', 'type': 'WorkItemReference'}
    }

    def __init__(self, point_assignments=None, test_case=None):
        super(SuiteTestCase, self).__init__()
        self.point_assignments = point_assignments
        self.test_case = test_case
