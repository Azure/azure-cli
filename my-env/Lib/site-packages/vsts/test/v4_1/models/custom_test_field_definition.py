# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CustomTestFieldDefinition(Model):
    """CustomTestFieldDefinition.

    :param field_id:
    :type field_id: int
    :param field_name:
    :type field_name: str
    :param field_type:
    :type field_type: object
    :param scope:
    :type scope: object
    """

    _attribute_map = {
        'field_id': {'key': 'fieldId', 'type': 'int'},
        'field_name': {'key': 'fieldName', 'type': 'str'},
        'field_type': {'key': 'fieldType', 'type': 'object'},
        'scope': {'key': 'scope', 'type': 'object'}
    }

    def __init__(self, field_id=None, field_name=None, field_type=None, scope=None):
        super(CustomTestFieldDefinition, self).__init__()
        self.field_id = field_id
        self.field_name = field_name
        self.field_type = field_type
        self.scope = scope
