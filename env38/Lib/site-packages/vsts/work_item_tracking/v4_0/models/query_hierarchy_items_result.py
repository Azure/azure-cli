# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class QueryHierarchyItemsResult(Model):
    """QueryHierarchyItemsResult.

    :param count:
    :type count: int
    :param has_more:
    :type has_more: bool
    :param value:
    :type value: list of :class:`QueryHierarchyItem <work-item-tracking.v4_0.models.QueryHierarchyItem>`
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'has_more': {'key': 'hasMore', 'type': 'bool'},
        'value': {'key': 'value', 'type': '[QueryHierarchyItem]'}
    }

    def __init__(self, count=None, has_more=None, value=None):
        super(QueryHierarchyItemsResult, self).__init__()
        self.count = count
        self.has_more = has_more
        self.value = value
