# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class OperationResult(Model):
    """OperationResult.

    :param errors: List of error codes paired with their corresponding error messages
    :type errors: list of { key: int; value: str }
    :param is_success: Success status of the operation
    :type is_success: bool
    :param member_id: Identifier of the Member being acted upon
    :type member_id: str
    :param result: Result of the MemberEntitlement after the operation
    :type result: :class:`MemberEntitlement <member-entitlement-management.v4_0.models.MemberEntitlement>`
    """

    _attribute_map = {
        'errors': {'key': 'errors', 'type': '[{ key: int; value: str }]'},
        'is_success': {'key': 'isSuccess', 'type': 'bool'},
        'member_id': {'key': 'memberId', 'type': 'str'},
        'result': {'key': 'result', 'type': 'MemberEntitlement'}
    }

    def __init__(self, errors=None, is_success=None, member_id=None, result=None):
        super(OperationResult, self).__init__()
        self.errors = errors
        self.is_success = is_success
        self.member_id = member_id
        self.result = result
