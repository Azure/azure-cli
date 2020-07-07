# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource_reference import WorkItemTrackingResourceReference


class WorkItemUpdate(WorkItemTrackingResourceReference):
    """WorkItemUpdate.

    :param url:
    :type url: str
    :param fields:
    :type fields: dict
    :param id:
    :type id: int
    :param relations:
    :type relations: :class:`WorkItemRelationUpdates <work-item-tracking.v4_0.models.WorkItemRelationUpdates>`
    :param rev:
    :type rev: int
    :param revised_by:
    :type revised_by: :class:`IdentityReference <work-item-tracking.v4_0.models.IdentityReference>`
    :param revised_date:
    :type revised_date: datetime
    :param work_item_id:
    :type work_item_id: int
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        'fields': {'key': 'fields', 'type': '{WorkItemFieldUpdate}'},
        'id': {'key': 'id', 'type': 'int'},
        'relations': {'key': 'relations', 'type': 'WorkItemRelationUpdates'},
        'rev': {'key': 'rev', 'type': 'int'},
        'revised_by': {'key': 'revisedBy', 'type': 'IdentityReference'},
        'revised_date': {'key': 'revisedDate', 'type': 'iso-8601'},
        'work_item_id': {'key': 'workItemId', 'type': 'int'}
    }

    def __init__(self, url=None, fields=None, id=None, relations=None, rev=None, revised_by=None, revised_date=None, work_item_id=None):
        super(WorkItemUpdate, self).__init__(url=url)
        self.fields = fields
        self.id = id
        self.relations = relations
        self.rev = rev
        self.revised_by = revised_by
        self.revised_date = revised_date
        self.work_item_id = work_item_id
