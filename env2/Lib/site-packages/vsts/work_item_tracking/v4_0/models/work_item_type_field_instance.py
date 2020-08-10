# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_field_reference import WorkItemFieldReference


class WorkItemTypeFieldInstance(WorkItemFieldReference):
    """WorkItemTypeFieldInstance.

    :param name:
    :type name: str
    :param reference_name:
    :type reference_name: str
    :param url:
    :type url: str
    :param always_required:
    :type always_required: bool
    :param field:
    :type field: :class:`WorkItemFieldReference <work-item-tracking.v4_0.models.WorkItemFieldReference>`
    :param help_text:
    :type help_text: str
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'reference_name': {'key': 'referenceName', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'always_required': {'key': 'alwaysRequired', 'type': 'bool'},
        'field': {'key': 'field', 'type': 'WorkItemFieldReference'},
        'help_text': {'key': 'helpText', 'type': 'str'}
    }

    def __init__(self, name=None, reference_name=None, url=None, always_required=None, field=None, help_text=None):
        super(WorkItemTypeFieldInstance, self).__init__(name=name, reference_name=reference_name, url=url)
        self.always_required = always_required
        self.field = field
        self.help_text = help_text
