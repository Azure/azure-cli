# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource import WorkItemTrackingResource


class WorkItem(WorkItemTrackingResource):
    """WorkItem.

    :param url:
    :type url: str
    :param _links:
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_0.models.ReferenceLinks>`
    :param fields:
    :type fields: dict
    :param id:
    :type id: int
    :param relations:
    :type relations: list of :class:`WorkItemRelation <work-item-tracking.v4_0.models.WorkItemRelation>`
    :param rev:
    :type rev: int
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'fields': {'key': 'fields', 'type': '{object}'},
        'id': {'key': 'id', 'type': 'int'},
        'relations': {'key': 'relations', 'type': '[WorkItemRelation]'},
        'rev': {'key': 'rev', 'type': 'int'}
    }

    def __init__(self, url=None, _links=None, fields=None, id=None, relations=None, rev=None):
        super(WorkItem, self).__init__(url=url, _links=_links)
        self.fields = fields
        self.id = id
        self.relations = relations
        self.rev = rev
