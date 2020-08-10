# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CustomTestField(Model):
    """CustomTestField.

    :param field_name:
    :type field_name: str
    :param value:
    :type value: object
    """

    _attribute_map = {
        'field_name': {'key': 'fieldName', 'type': 'str'},
        'value': {'key': 'value', 'type': 'object'}
    }

    def __init__(self, field_name=None, value=None):
        super(CustomTestField, self).__init__()
        self.field_name = field_name
        self.value = value
