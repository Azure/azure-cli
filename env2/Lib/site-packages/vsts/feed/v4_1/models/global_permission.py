# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GlobalPermission(Model):
    """GlobalPermission.

    :param identity_descriptor:
    :type identity_descriptor: :class:`str <packaging.v4_1.models.str>`
    :param role:
    :type role: object
    """

    _attribute_map = {
        'identity_descriptor': {'key': 'identityDescriptor', 'type': 'str'},
        'role': {'key': 'role', 'type': 'object'}
    }

    def __init__(self, identity_descriptor=None, role=None):
        super(GlobalPermission, self).__init__()
        self.identity_descriptor = identity_descriptor
        self.role = role
