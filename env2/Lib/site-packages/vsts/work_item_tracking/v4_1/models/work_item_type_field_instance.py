# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_type_field_instance_base import WorkItemTypeFieldInstanceBase


class WorkItemTypeFieldInstance(WorkItemTypeFieldInstanceBase):
    """WorkItemTypeFieldInstance.

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
    :param allowed_values: The list of field allowed values.
    :type allowed_values: list of str
    :param default_value: Represents the default value of the field.
    :type default_value: str
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'reference_name': {'key': 'referenceName', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'always_required': {'key': 'alwaysRequired', 'type': 'bool'},
        'dependent_fields': {'key': 'dependentFields', 'type': '[WorkItemFieldReference]'},
        'help_text': {'key': 'helpText', 'type': 'str'},
        'allowed_values': {'key': 'allowedValues', 'type': '[str]'},
        'default_value': {'key': 'defaultValue', 'type': 'str'}
    }

    def __init__(self, name=None, reference_name=None, url=None, always_required=None, dependent_fields=None, help_text=None, allowed_values=None, default_value=None):
        super(WorkItemTypeFieldInstance, self).__init__(name=name, reference_name=reference_name, url=url, always_required=always_required, dependent_fields=dependent_fields, help_text=help_text)
        self.allowed_values = allowed_values
        self.default_value = default_value
