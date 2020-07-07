# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .member_entitlements_response_base import MemberEntitlementsResponseBase


class MemberEntitlementsPostResponse(MemberEntitlementsResponseBase):
    """MemberEntitlementsPostResponse.

    :param is_success: True if all operations were successful.
    :type is_success: bool
    :param member_entitlement: Result of the member entitlement after the operations. have been applied
    :type member_entitlement: :class:`MemberEntitlement <member-entitlement-management.v4_1.models.MemberEntitlement>`
    :param operation_result: Operation result
    :type operation_result: :class:`OperationResult <member-entitlement-management.v4_1.models.OperationResult>`
    """

    _attribute_map = {
        'is_success': {'key': 'isSuccess', 'type': 'bool'},
        'member_entitlement': {'key': 'memberEntitlement', 'type': 'MemberEntitlement'},
        'operation_result': {'key': 'operationResult', 'type': 'OperationResult'}
    }

    def __init__(self, is_success=None, member_entitlement=None, operation_result=None):
        super(MemberEntitlementsPostResponse, self).__init__(is_success=is_success, member_entitlement=member_entitlement)
        self.operation_result = operation_result
