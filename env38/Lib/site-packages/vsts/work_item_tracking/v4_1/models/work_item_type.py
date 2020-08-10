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
    :param _links: Link references to related REST resources.
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_1.models.ReferenceLinks>`
    :param color: The color.
    :type color: str
    :param description: The description of the work item type.
    :type description: str
    :param field_instances: The fields that exist on the work item type.
    :type field_instances: list of :class:`WorkItemTypeFieldInstance <work-item-tracking.v4_1.models.WorkItemTypeFieldInstance>`
    :param fields: The fields that exist on the work item type.
    :type fields: list of :class:`WorkItemTypeFieldInstance <work-item-tracking.v4_1.models.WorkItemTypeFieldInstance>`
    :param icon: The icon of the work item type.
    :type icon: :class:`WorkItemIcon <work-item-tracking.v4_1.models.WorkItemIcon>`
    :param is_disabled: True if work item type is disabled
    :type is_disabled: bool
    :param name: Gets the name of the work item type.
    :type name: str
    :param reference_name: The reference name of the work item type.
    :type reference_name: str
    :param transitions: Gets the various state transition mappings in the work item type.
    :type transitions: dict
    :param xml_form: The XML form.
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
        'is_disabled': {'key': 'isDisabled', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'reference_name': {'key': 'referenceName', 'type': 'str'},
        'transitions': {'key': 'transitions', 'type': '{[WorkItemStateTransition]}'},
        'xml_form': {'key': 'xmlForm', 'type': 'str'}
    }

    def __init__(self, url=None, _links=None, color=None, description=None, field_instances=None, fields=None, icon=None, is_disabled=None, name=None, reference_name=None, transitions=None, xml_form=None):
        super(WorkItemType, self).__init__(url=url, _links=_links)
        self.color = color
        self.description = description
        self.field_instances = field_instances
        self.fields = fields
        self.icon = icon
        self.is_disabled = is_disabled
        self.name = name
        self.reference_name = reference_name
        self.transitions = transitions
        self.xml_form = xml_form
