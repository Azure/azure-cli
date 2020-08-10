# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemQueryResult(Model):
    """WorkItemQueryResult.

    :param as_of:
    :type as_of: datetime
    :param columns:
    :type columns: list of :class:`WorkItemFieldReference <work-item-tracking.v4_0.models.WorkItemFieldReference>`
    :param query_result_type:
    :type query_result_type: object
    :param query_type:
    :type query_type: object
    :param sort_columns:
    :type sort_columns: list of :class:`WorkItemQuerySortColumn <work-item-tracking.v4_0.models.WorkItemQuerySortColumn>`
    :param work_item_relations:
    :type work_item_relations: list of :class:`WorkItemLink <work-item-tracking.v4_0.models.WorkItemLink>`
    :param work_items:
    :type work_items: list of :class:`WorkItemReference <work-item-tracking.v4_0.models.WorkItemReference>`
    """

    _attribute_map = {
        'as_of': {'key': 'asOf', 'type': 'iso-8601'},
        'columns': {'key': 'columns', 'type': '[WorkItemFieldReference]'},
        'query_result_type': {'key': 'queryResultType', 'type': 'object'},
        'query_type': {'key': 'queryType', 'type': 'object'},
        'sort_columns': {'key': 'sortColumns', 'type': '[WorkItemQuerySortColumn]'},
        'work_item_relations': {'key': 'workItemRelations', 'type': '[WorkItemLink]'},
        'work_items': {'key': 'workItems', 'type': '[WorkItemReference]'}
    }

    def __init__(self, as_of=None, columns=None, query_result_type=None, query_type=None, sort_columns=None, work_item_relations=None, work_items=None):
        super(WorkItemQueryResult, self).__init__()
        self.as_of = as_of
        self.columns = columns
        self.query_result_type = query_result_type
        self.query_type = query_type
        self.sort_columns = sort_columns
        self.work_item_relations = work_item_relations
        self.work_items = work_items
