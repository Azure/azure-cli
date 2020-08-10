# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ActionDefinition(Model):
    """ActionDefinition.

    :param bit: The bit mask integer for this action. Must be a power of 2.
    :type bit: int
    :param display_name: The localized display name for this action.
    :type display_name: str
    :param name: The non-localized name for this action.
    :type name: str
    :param namespace_id: The namespace that this action belongs to.  This will only be used for reading from the database.
    :type namespace_id: str
    """

    _attribute_map = {
        'bit': {'key': 'bit', 'type': 'int'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'namespace_id': {'key': 'namespaceId', 'type': 'str'}
    }

    def __init__(self, bit=None, display_name=None, name=None, namespace_id=None):
        super(ActionDefinition, self).__init__()
        self.bit = bit
        self.display_name = display_name
        self.name = name
        self.namespace_id = namespace_id
