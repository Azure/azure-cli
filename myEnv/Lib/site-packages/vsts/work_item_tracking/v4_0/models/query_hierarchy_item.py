# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource import WorkItemTrackingResource


class QueryHierarchyItem(WorkItemTrackingResource):
    """QueryHierarchyItem.

    :param url:
    :type url: str
    :param _links:
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_0.models.ReferenceLinks>`
    :param children:
    :type children: list of :class:`QueryHierarchyItem <work-item-tracking.v4_0.models.QueryHierarchyItem>`
    :param clauses:
    :type clauses: :class:`WorkItemQueryClause <work-item-tracking.v4_0.models.WorkItemQueryClause>`
    :param columns:
    :type columns: list of :class:`WorkItemFieldReference <work-item-tracking.v4_0.models.WorkItemFieldReference>`
    :param created_by:
    :type created_by: :class:`IdentityReference <work-item-tracking.v4_0.models.IdentityReference>`
    :param created_date:
    :type created_date: datetime
    :param filter_options:
    :type filter_options: object
    :param has_children:
    :type has_children: bool
    :param id:
    :type id: str
    :param is_deleted:
    :type is_deleted: bool
    :param is_folder:
    :type is_folder: bool
    :param is_invalid_syntax:
    :type is_invalid_syntax: bool
    :param is_public:
    :type is_public: bool
    :param last_modified_by:
    :type last_modified_by: :class:`IdentityReference <work-item-tracking.v4_0.models.IdentityReference>`
    :param last_modified_date:
    :type last_modified_date: datetime
    :param link_clauses:
    :type link_clauses: :class:`WorkItemQueryClause <work-item-tracking.v4_0.models.WorkItemQueryClause>`
    :param name:
    :type name: str
    :param path:
    :type path: str
    :param query_type:
    :type query_type: object
    :param sort_columns:
    :type sort_columns: list of :class:`WorkItemQuerySortColumn <work-item-tracking.v4_0.models.WorkItemQuerySortColumn>`
    :param source_clauses:
    :type source_clauses: :class:`WorkItemQueryClause <work-item-tracking.v4_0.models.WorkItemQueryClause>`
    :param target_clauses:
    :type target_clauses: :class:`WorkItemQueryClause <work-item-tracking.v4_0.models.WorkItemQueryClause>`
    :param wiql:
    :type wiql: str
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'children': {'key': 'children', 'type': '[QueryHierarchyItem]'},
        'clauses': {'key': 'clauses', 'type': 'WorkItemQueryClause'},
        'columns': {'key': 'columns', 'type': '[WorkItemFieldReference]'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityReference'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'filter_options': {'key': 'filterOptions', 'type': 'object'},
        'has_children': {'key': 'hasChildren', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'str'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'is_folder': {'key': 'isFolder', 'type': 'bool'},
        'is_invalid_syntax': {'key': 'isInvalidSyntax', 'type': 'bool'},
        'is_public': {'key': 'isPublic', 'type': 'bool'},
        'last_modified_by': {'key': 'lastModifiedBy', 'type': 'IdentityReference'},
        'last_modified_date': {'key': 'lastModifiedDate', 'type': 'iso-8601'},
        'link_clauses': {'key': 'linkClauses', 'type': 'WorkItemQueryClause'},
        'name': {'key': 'name', 'type': 'str'},
        'path': {'key': 'path', 'type': 'str'},
        'query_type': {'key': 'queryType', 'type': 'object'},
        'sort_columns': {'key': 'sortColumns', 'type': '[WorkItemQuerySortColumn]'},
        'source_clauses': {'key': 'sourceClauses', 'type': 'WorkItemQueryClause'},
        'target_clauses': {'key': 'targetClauses', 'type': 'WorkItemQueryClause'},
        'wiql': {'key': 'wiql', 'type': 'str'}
    }

    def __init__(self, url=None, _links=None, children=None, clauses=None, columns=None, created_by=None, created_date=None, filter_options=None, has_children=None, id=None, is_deleted=None, is_folder=None, is_invalid_syntax=None, is_public=None, last_modified_by=None, last_modified_date=None, link_clauses=None, name=None, path=None, query_type=None, sort_columns=None, source_clauses=None, target_clauses=None, wiql=None):
        super(QueryHierarchyItem, self).__init__(url=url, _links=_links)
        self.children = children
        self.clauses = clauses
        self.columns = columns
        self.created_by = created_by
        self.created_date = created_date
        self.filter_options = filter_options
        self.has_children = has_children
        self.id = id
        self.is_deleted = is_deleted
        self.is_folder = is_folder
        self.is_invalid_syntax = is_invalid_syntax
        self.is_public = is_public
        self.last_modified_by = last_modified_by
        self.last_modified_date = last_modified_date
        self.link_clauses = link_clauses
        self.name = name
        self.path = path
        self.query_type = query_type
        self.sort_columns = sort_columns
        self.source_clauses = source_clauses
        self.target_clauses = target_clauses
        self.wiql = wiql
