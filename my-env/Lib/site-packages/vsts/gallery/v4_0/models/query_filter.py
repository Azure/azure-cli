# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class QueryFilter(Model):
    """QueryFilter.

    :param criteria: The filter values define the set of values in this query. They are applied based on the QueryFilterType.
    :type criteria: list of :class:`FilterCriteria <gallery.v4_0.models.FilterCriteria>`
    :param direction: The PagingDirection is applied to a paging token if one exists. If not the direction is ignored, and Forward from the start of the resultset is used. Direction should be left out of the request unless a paging token is used to help prevent future issues.
    :type direction: object
    :param page_number: The page number requested by the user. If not provided 1 is assumed by default.
    :type page_number: int
    :param page_size: The page size defines the number of results the caller wants for this filter. The count can't exceed the overall query size limits.
    :type page_size: int
    :param paging_token: The paging token is a distinct type of filter and the other filter fields are ignored. The paging token represents the continuation of a previously executed query. The information about where in the result and what fields are being filtered are embeded in the token.
    :type paging_token: str
    :param sort_by: Defines the type of sorting to be applied on the results. The page slice is cut of the sorted results only.
    :type sort_by: int
    :param sort_order: Defines the order of sorting, 1 for Ascending, 2 for Descending, else default ordering based on the SortBy value
    :type sort_order: int
    """

    _attribute_map = {
        'criteria': {'key': 'criteria', 'type': '[FilterCriteria]'},
        'direction': {'key': 'direction', 'type': 'object'},
        'page_number': {'key': 'pageNumber', 'type': 'int'},
        'page_size': {'key': 'pageSize', 'type': 'int'},
        'paging_token': {'key': 'pagingToken', 'type': 'str'},
        'sort_by': {'key': 'sortBy', 'type': 'int'},
        'sort_order': {'key': 'sortOrder', 'type': 'int'}
    }

    def __init__(self, criteria=None, direction=None, page_number=None, page_size=None, paging_token=None, sort_by=None, sort_order=None):
        super(QueryFilter, self).__init__()
        self.criteria = criteria
        self.direction = direction
        self.page_number = page_number
        self.page_size = page_size
        self.paging_token = paging_token
        self.sort_by = sort_by
        self.sort_order = sort_order
