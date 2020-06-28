# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestPlanCloneRequest(Model):
    """TestPlanCloneRequest.

    :param destination_test_plan:
    :type destination_test_plan: :class:`TestPlan <test.v4_0.models.TestPlan>`
    :param options:
    :type options: :class:`CloneOptions <test.v4_0.models.CloneOptions>`
    :param suite_ids:
    :type suite_ids: list of int
    """

    _attribute_map = {
        'destination_test_plan': {'key': 'destinationTestPlan', 'type': 'TestPlan'},
        'options': {'key': 'options', 'type': 'CloneOptions'},
        'suite_ids': {'key': 'suiteIds', 'type': '[int]'}
    }

    def __init__(self, destination_test_plan=None, options=None, suite_ids=None):
        super(TestPlanCloneRequest, self).__init__()
        self.destination_test_plan = destination_test_plan
        self.options = options
        self.suite_ids = suite_ids
