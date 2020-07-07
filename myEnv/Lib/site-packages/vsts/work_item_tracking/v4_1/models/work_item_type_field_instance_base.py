# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_field_reference import WorkItemFieldReference


class WorkItemTypeFieldInstanceBase(WorkItemFieldReference):
    """WorkItemTypeFieldInstanceBase.

    :param name: The name of the field.
    :type name: str
    :param reference_name: The reference name of the field.
    :type reference_name: str
    :param url: The REST URL of the resource.
    :type url: str
    :param always_required: Indicates whether field value is always required.
    :type always_required: bool
    :param dependent_fields: The list of dependent fields.
    :type dependent_fields: list of :class:`WorkItemFieldReference <work-item-tracking.v4_1.models.WorkItemFieldReference>`
    :param help_text: Gets the help text for the field.
    :type help_text: str
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'reference_name': {'key': 'referenceName', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'always_required': {'key': 'alwaysRequired', 'type': 'bool'},
        'dependent_fields': {'key': 'dependentFields', 'type': '[WorkItemFieldReference]'},
        'help_text': {'key': 'helpText', 'type': 'str'}
    }

    def __init__(self, name=None, reference_name=None, url=None, always_required=None, dependent_fields=None, help_text=None):
        super(WorkItemTypeFieldInstanceBase, self).__init__(name=name, reference_name=reference_name, url=url)
        self.always_required = always_required
        self.dependent_fields = dependent_fields
        self.help_text = help_text
