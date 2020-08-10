# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UserEntitlementsResponseBase(Model):
    """UserEntitlementsResponseBase.

    :param is_success: True if all operations were successful.
    :type is_success: bool
    :param user_entitlement: Result of the user entitlement after the operations have been applied.
    :type user_entitlement: :class:`UserEntitlement <member-entitlement-management.v4_1.models.UserEntitlement>`
    """

    _attribute_map = {
        'is_success': {'key': 'isSuccess', 'type': 'bool'},
        'user_entitlement': {'key': 'userEntitlement', 'type': 'UserEntitlement'}
    }

    def __init__(self, is_success=None, user_entitlement=None):
        super(UserEntitlementsResponseBase, self).__init__()
        self.is_success = is_success
        self.user_entitlement = user_entitlement
