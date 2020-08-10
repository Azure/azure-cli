# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FrameworkIdentityInfo(Model):
    """FrameworkIdentityInfo.

    :param display_name:
    :type display_name: str
    :param identifier:
    :type identifier: str
    :param identity_type:
    :type identity_type: object
    :param role:
    :type role: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'identifier': {'key': 'identifier', 'type': 'str'},
        'identity_type': {'key': 'identityType', 'type': 'object'},
        'role': {'key': 'role', 'type': 'str'}
    }

    def __init__(self, display_name=None, identifier=None, identity_type=None, role=None):
        super(FrameworkIdentityInfo, self).__init__()
        self.display_name = display_name
        self.identifier = identifier
        self.identity_type = identity_type
        self.role = role
