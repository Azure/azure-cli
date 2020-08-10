# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestSummaryForWorkItem(Model):
    """TestSummaryForWorkItem.

    :param summary:
    :type summary: :class:`AggregatedDataForResultTrend <test.v4_0.models.AggregatedDataForResultTrend>`
    :param work_item:
    :type work_item: :class:`WorkItemReference <test.v4_0.models.WorkItemReference>`
    """

    _attribute_map = {
        'summary': {'key': 'summary', 'type': 'AggregatedDataForResultTrend'},
        'work_item': {'key': 'workItem', 'type': 'WorkItemReference'}
    }

    def __init__(self, summary=None, work_item=None):
        super(TestSummaryForWorkItem, self).__init__()
        self.summary = summary
        self.work_item = work_item
