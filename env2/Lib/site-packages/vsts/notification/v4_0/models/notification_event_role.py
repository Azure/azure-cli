# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationEventRole(Model):
    """NotificationEventRole.

    :param id: Gets or sets an Id for that role, this id is used by the event.
    :type id: str
    :param name: Gets or sets the Name for that role, this name is used for UI display.
    :type name: str
    :param supports_groups: Gets or sets whether this role can be a group or just an individual user
    :type supports_groups: bool
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'supports_groups': {'key': 'supportsGroups', 'type': 'bool'}
    }

    def __init__(self, id=None, name=None, supports_groups=None):
        super(NotificationEventRole, self).__init__()
        self.id = id
        self.name = name
        self.supports_groups = supports_groups
