# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FieldModel(Model):
    """FieldModel.

    :param description: Description about field
    :type description: str
    :param id: ID of the field
    :type id: str
    :param name: Name of the field
    :type name: str
    :param pick_list: Reference to picklist in this field
    :type pick_list: :class:`PickListMetadataModel <work-item-tracking.v4_1.models.PickListMetadataModel>`
    :param type: Type of field
    :type type: object
    :param url: Url to the field
    :type url: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'pick_list': {'key': 'pickList', 'type': 'PickListMetadataModel'},
        'type': {'key': 'type', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, description=None, id=None, name=None, pick_list=None, type=None, url=None):
        super(FieldModel, self).__init__()
        self.description = description
        self.id = id
        self.name = name
        self.pick_list = pick_list
        self.type = type
        self.url = url
