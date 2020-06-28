# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccessControlList(Model):
    """AccessControlList.

    :param aces_dictionary: Storage of permissions keyed on the identity the permission is for.
    :type aces_dictionary: dict
    :param include_extended_info: True if this ACL holds ACEs that have extended information.
    :type include_extended_info: bool
    :param inherit_permissions: True if the given token inherits permissions from parents.
    :type inherit_permissions: bool
    :param token: The token that this AccessControlList is for.
    :type token: str
    """

    _attribute_map = {
        'aces_dictionary': {'key': 'acesDictionary', 'type': '{AccessControlEntry}'},
        'include_extended_info': {'key': 'includeExtendedInfo', 'type': 'bool'},
        'inherit_permissions': {'key': 'inheritPermissions', 'type': 'bool'},
        'token': {'key': 'token', 'type': 'str'}
    }

    def __init__(self, aces_dictionary=None, include_extended_info=None, inherit_permissions=None, token=None):
        super(AccessControlList, self).__init__()
        self.aces_dictionary = aces_dictionary
        self.include_extended_info = include_extended_info
        self.inherit_permissions = inherit_permissions
        self.token = token
