# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemTypeFieldModel(Model):
    """WorkItemTypeFieldModel.

    :param allow_groups:
    :type allow_groups: bool
    :param default_value:
    :type default_value: str
    :param name:
    :type name: str
    :param pick_list:
    :type pick_list: :class:`PickListMetadataModel <work-item-tracking.v4_1.models.PickListMetadataModel>`
    :param read_only:
    :type read_only: bool
    :param reference_name:
    :type reference_name: str
    :param required:
    :type required: bool
    :param type:
    :type type: object
    :param url:
    :type url: str
    """

    _attribute_map = {
        'allow_groups': {'key': 'allowGroups', 'type': 'bool'},
        'default_value': {'key': 'defaultValue', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'pick_list': {'key': 'pickList', 'type': 'PickListMetadataModel'},
        'read_only': {'key': 'readOnly', 'type': 'bool'},
        'reference_name': {'key': 'referenceName', 'type': 'str'},
        'required': {'key': 'required', 'type': 'bool'},
        'type': {'key': 'type', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, allow_groups=None, default_value=None, name=None, pick_list=None, read_only=None, reference_name=None, required=None, type=None, url=None):
        super(WorkItemTypeFieldModel, self).__init__()
        self.allow_groups = allow_groups
        self.default_value = default_value
        self.name = name
        self.pick_list = pick_list
        self.read_only = read_only
        self.reference_name = reference_name
        self.required = required
        self.type = type
        self.url = url
