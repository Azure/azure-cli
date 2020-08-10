# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .user_entitlements_response_base import UserEntitlementsResponseBase


class UserEntitlementsPostResponse(UserEntitlementsResponseBase):
    """UserEntitlementsPostResponse.

    :param is_success: True if all operations were successful.
    :type is_success: bool
    :param user_entitlement: Result of the user entitlement after the operations have been applied.
    :type user_entitlement: :class:`UserEntitlement <member-entitlement-management.v4_1.models.UserEntitlement>`
    :param operation_result: Operation result.
    :type operation_result: :class:`UserEntitlementOperationResult <member-entitlement-management.v4_1.models.UserEntitlementOperationResult>`
    """

    _attribute_map = {
        'is_success': {'key': 'isSuccess', 'type': 'bool'},
        'user_entitlement': {'key': 'userEntitlement', 'type': 'UserEntitlement'},
        'operation_result': {'key': 'operationResult', 'type': 'UserEntitlementOperationResult'}
    }

    def __init__(self, is_success=None, user_entitlement=None, operation_result=None):
        super(UserEntitlementsPostResponse, self).__init__(is_success=is_success, user_entitlement=user_entitlement)
        self.operation_result = operation_result
