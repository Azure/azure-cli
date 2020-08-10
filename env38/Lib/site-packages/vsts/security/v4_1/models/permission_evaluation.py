# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PermissionEvaluation(Model):
    """PermissionEvaluation.

    :param permissions: Permission bit for this evaluated permission.
    :type permissions: int
    :param security_namespace_id: Security namespace identifier for this evaluated permission.
    :type security_namespace_id: str
    :param token: Security namespace-specific token for this evaluated permission.
    :type token: str
    :param value: Permission evaluation value.
    :type value: bool
    """

    _attribute_map = {
        'permissions': {'key': 'permissions', 'type': 'int'},
        'security_namespace_id': {'key': 'securityNamespaceId', 'type': 'str'},
        'token': {'key': 'token', 'type': 'str'},
        'value': {'key': 'value', 'type': 'bool'}
    }

    def __init__(self, permissions=None, security_namespace_id=None, token=None, value=None):
        super(PermissionEvaluation, self).__init__()
        self.permissions = permissions
        self.security_namespace_id = security_namespace_id
        self.token = token
        self.value = value
