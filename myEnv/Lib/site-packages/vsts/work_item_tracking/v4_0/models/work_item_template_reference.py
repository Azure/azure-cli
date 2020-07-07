# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource import WorkItemTrackingResource


class WorkItemTemplateReference(WorkItemTrackingResource):
    """WorkItemTemplateReference.

    :param url:
    :type url: str
    :param _links:
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_0.models.ReferenceLinks>`
    :param description:
    :type description: str
    :param id:
    :type id: str
    :param name:
    :type name: str
    :param work_item_type_name:
    :type work_item_type_name: str
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'work_item_type_name': {'key': 'workItemTypeName', 'type': 'str'}
    }

    def __init__(self, url=None, _links=None, description=None, id=None, name=None, work_item_type_name=None):
        super(WorkItemTemplateReference, self).__init__(url=url, _links=_links)
        self.description = description
        self.id = id
        self.name = name
        self.work_item_type_name = work_item_type_name
