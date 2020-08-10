# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FeedPermission(Model):
    """FeedPermission.

    :param display_name: Display name for the identity
    :type display_name: str
    :param identity_descriptor:
    :type identity_descriptor: :class:`str <packaging.v4_1.models.str>`
    :param identity_id:
    :type identity_id: str
    :param role:
    :type role: object
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'identity_descriptor': {'key': 'identityDescriptor', 'type': 'str'},
        'identity_id': {'key': 'identityId', 'type': 'str'},
        'role': {'key': 'role', 'type': 'object'}
    }

    def __init__(self, display_name=None, identity_descriptor=None, identity_id=None, role=None):
        super(FeedPermission, self).__init__()
        self.display_name = display_name
        self.identity_descriptor = identity_descriptor
        self.identity_id = identity_id
        self.role = role
