# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource import WorkItemTrackingResource


class WorkItemField(WorkItemTrackingResource):
    """WorkItemField.

    :param url:
    :type url: str
    :param _links: Link references to related REST resources.
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_1.models.ReferenceLinks>`
    :param description: The description of the field.
    :type description: str
    :param is_identity: Indicates whether this field is an identity field.
    :type is_identity: bool
    :param is_picklist: Indicates whether this instance is picklist.
    :type is_picklist: bool
    :param is_picklist_suggested: Indicates whether this instance is a suggested picklist .
    :type is_picklist_suggested: bool
    :param name: The name of the field.
    :type name: str
    :param read_only: Indicates whether the field is [read only].
    :type read_only: bool
    :param reference_name: The reference name of the field.
    :type reference_name: str
    :param supported_operations: The supported operations on this field.
    :type supported_operations: list of :class:`WorkItemFieldOperation <work-item-tracking.v4_1.models.WorkItemFieldOperation>`
    :param type: The type of the field.
    :type type: object
    :param usage: The usage of the field.
    :type usage: object
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'description': {'key': 'description', 'type': 'str'},
        'is_identity': {'key': 'isIdentity', 'type': 'bool'},
        'is_picklist': {'key': 'isPicklist', 'type': 'bool'},
        'is_picklist_suggested': {'key': 'isPicklistSuggested', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'read_only': {'key': 'readOnly', 'type': 'bool'},
        'reference_name': {'key': 'referenceName', 'type': 'str'},
        'supported_operations': {'key': 'supportedOperations', 'type': '[WorkItemFieldOperation]'},
        'type': {'key': 'type', 'type': 'object'},
        'usage': {'key': 'usage', 'type': 'object'}
    }

    def __init__(self, url=None, _links=None, description=None, is_identity=None, is_picklist=None, is_picklist_suggested=None, name=None, read_only=None, reference_name=None, supported_operations=None, type=None, usage=None):
        super(WorkItemField, self).__init__(url=url, _links=_links)
        self.description = description
        self.is_identity = is_identity
        self.is_picklist = is_picklist
        self.is_picklist_suggested = is_picklist_suggested
        self.name = name
        self.read_only = read_only
        self.reference_name = reference_name
        self.supported_operations = supported_operations
        self.type = type
        self.usage = usage
