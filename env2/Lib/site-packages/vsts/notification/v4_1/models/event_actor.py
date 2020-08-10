# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class EventActor(Model):
    """EventActor.

    :param id: Required: This is the identity of the user for the specified role.
    :type id: str
    :param role: Required: The event specific name of a role.
    :type role: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'role': {'key': 'role', 'type': 'str'}
    }

    def __init__(self, id=None, role=None):
        super(EventActor, self).__init__()
        self.id = id
        self.role = role
