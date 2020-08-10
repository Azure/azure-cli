# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UserExtensionPolicy(Model):
    """UserExtensionPolicy.

    :param display_name: User display name that this policy refers to
    :type display_name: str
    :param permissions: The extension policy applied to the user
    :type permissions: :class:`ExtensionPolicy <microsoft.-visual-studio.-services.-gallery.-web-api.v4_0.models.ExtensionPolicy>`
    :param user_id: User id that this policy refers to
    :type user_id: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'permissions': {'key': 'permissions', 'type': 'ExtensionPolicy'},
        'user_id': {'key': 'userId', 'type': 'str'}
    }

    def __init__(self, display_name=None, permissions=None, user_id=None):
        super(UserExtensionPolicy, self).__init__()
        self.display_name = display_name
        self.permissions = permissions
        self.user_id = user_id
