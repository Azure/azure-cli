# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestToWorkItemLinks(Model):
    """TestToWorkItemLinks.

    :param test:
    :type test: :class:`TestMethod <test.v4_1.models.TestMethod>`
    :param work_items:
    :type work_items: list of :class:`WorkItemReference <test.v4_1.models.WorkItemReference>`
    """

    _attribute_map = {
        'test': {'key': 'test', 'type': 'TestMethod'},
        'work_items': {'key': 'workItems', 'type': '[WorkItemReference]'}
    }

    def __init__(self, test=None, work_items=None):
        super(TestToWorkItemLinks, self).__init__()
        self.test = test
        self.work_items = work_items
