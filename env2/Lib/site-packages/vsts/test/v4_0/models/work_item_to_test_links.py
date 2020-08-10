# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemToTestLinks(Model):
    """WorkItemToTestLinks.

    :param tests:
    :type tests: list of :class:`TestMethod <test.v4_0.models.TestMethod>`
    :param work_item:
    :type work_item: :class:`WorkItemReference <test.v4_0.models.WorkItemReference>`
    """

    _attribute_map = {
        'tests': {'key': 'tests', 'type': '[TestMethod]'},
        'work_item': {'key': 'workItem', 'type': 'WorkItemReference'}
    }

    def __init__(self, tests=None, work_item=None):
        super(WorkItemToTestLinks, self).__init__()
        self.tests = tests
        self.work_item = work_item
