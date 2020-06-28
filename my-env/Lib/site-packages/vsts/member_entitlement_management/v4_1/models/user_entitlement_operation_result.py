# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UserEntitlementOperationResult(Model):
    """UserEntitlementOperationResult.

    :param errors: List of error codes paired with their corresponding error messages.
    :type errors: list of { key: int; value: str }
    :param is_success: Success status of the operation.
    :type is_success: bool
    :param result: Result of the MemberEntitlement after the operation.
    :type result: :class:`UserEntitlement <member-entitlement-management.v4_1.models.UserEntitlement>`
    :param user_id: Identifier of the Member being acted upon.
    :type user_id: str
    """

    _attribute_map = {
        'errors': {'key': 'errors', 'type': '[{ key: int; value: str }]'},
        'is_success': {'key': 'isSuccess', 'type': 'bool'},
        'result': {'key': 'result', 'type': 'UserEntitlement'},
        'user_id': {'key': 'userId', 'type': 'str'}
    }

    def __init__(self, errors=None, is_success=None, result=None, user_id=None):
        super(UserEntitlementOperationResult, self).__init__()
        self.errors = errors
        self.is_success = is_success
        self.result = result
        self.user_id = user_id
