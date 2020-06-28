# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountMyWorkResult(Model):
    """AccountMyWorkResult.

    :param query_size_limit_exceeded: True, when length of WorkItemDetails is same as the limit
    :type query_size_limit_exceeded: bool
    :param work_item_details: WorkItem Details
    :type work_item_details: list of :class:`AccountWorkWorkItemModel <work-item-tracking.v4_0.models.AccountWorkWorkItemModel>`
    """

    _attribute_map = {
        'query_size_limit_exceeded': {'key': 'querySizeLimitExceeded', 'type': 'bool'},
        'work_item_details': {'key': 'workItemDetails', 'type': '[AccountWorkWorkItemModel]'}
    }

    def __init__(self, query_size_limit_exceeded=None, work_item_details=None):
        super(AccountMyWorkResult, self).__init__()
        self.query_size_limit_exceeded = query_size_limit_exceeded
        self.work_item_details = work_item_details
