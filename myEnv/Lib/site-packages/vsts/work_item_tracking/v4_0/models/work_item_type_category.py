# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource import WorkItemTrackingResource


class WorkItemTypeCategory(WorkItemTrackingResource):
    """WorkItemTypeCategory.

    :param url:
    :type url: str
    :param _links:
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_0.models.ReferenceLinks>`
    :param default_work_item_type:
    :type default_work_item_type: :class:`WorkItemTypeReference <work-item-tracking.v4_0.models.WorkItemTypeReference>`
    :param name:
    :type name: str
    :param reference_name:
    :type reference_name: str
    :param work_item_types:
    :type work_item_types: list of :class:`WorkItemTypeReference <work-item-tracking.v4_0.models.WorkItemTypeReference>`
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'default_work_item_type': {'key': 'defaultWorkItemType', 'type': 'WorkItemTypeReference'},
        'name': {'key': 'name', 'type': 'str'},
        'reference_name': {'key': 'referenceName', 'type': 'str'},
        'work_item_types': {'key': 'workItemTypes', 'type': '[WorkItemTypeReference]'}
    }

    def __init__(self, url=None, _links=None, default_work_item_type=None, name=None, reference_name=None, work_item_types=None):
        super(WorkItemTypeCategory, self).__init__(url=url, _links=_links)
        self.default_work_item_type = default_work_item_type
        self.name = name
        self.reference_name = reference_name
        self.work_item_types = work_item_types
