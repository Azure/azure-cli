# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationEventField(Model):
    """NotificationEventField.

    :param field_type: Gets or sets the type of this field.
    :type field_type: :class:`NotificationEventFieldType <notification.v4_1.models.NotificationEventFieldType>`
    :param id: Gets or sets the unique identifier of this field.
    :type id: str
    :param name: Gets or sets the name of this field.
    :type name: str
    :param path: Gets or sets the path to the field in the event object. This path can be either Json Path or XPath, depending on if the event will be serialized into Json or XML
    :type path: str
    :param supported_scopes: Gets or sets the scopes that this field supports. If not specified then the event type scopes apply.
    :type supported_scopes: list of str
    """

    _attribute_map = {
        'field_type': {'key': 'fieldType', 'type': 'NotificationEventFieldType'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'path': {'key': 'path', 'type': 'str'},
        'supported_scopes': {'key': 'supportedScopes', 'type': '[str]'}
    }

    def __init__(self, field_type=None, id=None, name=None, path=None, supported_scopes=None):
        super(NotificationEventField, self).__init__()
        self.field_type = field_type
        self.id = id
        self.name = name
        self.path = path
        self.supported_scopes = supported_scopes
