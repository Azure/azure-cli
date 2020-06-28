# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource import WorkItemTrackingResource


class WorkItemType(WorkItemTrackingResource):
    """WorkItemType.

    :param url:
    :type url: str
    :param _links:
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_0.models.ReferenceLinks>`
    :param color:
    :type color: str
    :param description:
    :type description: str
    :param field_instances:
    :type field_instances: list of :class:`WorkItemTypeFieldInstance <work-item-tracking.v4_0.models.WorkItemTypeFieldInstance>`
    :param fields:
    :type fields: list of :class:`WorkItemTypeFieldInstance <work-item-tracking.v4_0.models.WorkItemTypeFieldInstance>`
    :param icon:
    :type icon: :class:`WorkItemIcon <work-item-tracking.v4_0.models.WorkItemIcon>`
    :param name:
    :type name: str
    :param transitions:
    :type transitions: dict
    :param xml_form:
    :type xml_form: str
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'color': {'key': 'color', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'field_instances': {'key': 'fieldInstances', 'type': '[WorkItemTypeFieldInstance]'},
        'fields': {'key': 'fields', 'type': '[WorkItemTypeFieldInstance]'},
        'icon': {'key': 'icon', 'type': 'WorkItemIcon'},
        'name': {'key': 'name', 'type': 'str'},
        'transitions': {'key': 'transitions', 'type': '{[WorkItemStateTransition]}'},
        'xml_form': {'key': 'xmlForm', 'type': 'str'}
    }

    def __init__(self, url=None, _links=None, color=None, description=None, field_instances=None, fields=None, icon=None, name=None, transitions=None, xml_form=None):
        super(WorkItemType, self).__init__(url=url, _links=_links)
        self.color = color
        self.description = description
        self.field_instances = field_instances
        self.fields = fields
        self.icon = icon
        self.name = name
        self.transitions = transitions
        self.xml_form = xml_form
