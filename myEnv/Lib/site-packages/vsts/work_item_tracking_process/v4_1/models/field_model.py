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

    :param description:
    :type description: str
    :param id:
    :type id: str
    :param is_identity:
    :type is_identity: bool
    :param name:
    :type name: str
    :param type:
    :type type: object
    :param url:
    :type url: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_identity': {'key': 'isIdentity', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, description=None, id=None, is_identity=None, name=None, type=None, url=None):
        super(FieldModel, self).__init__()
        self.description = description
        self.id = id
        self.is_identity = is_identity
        self.name = name
        self.type = type
        self.url = url
