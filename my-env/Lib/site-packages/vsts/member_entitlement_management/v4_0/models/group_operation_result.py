# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .base_operation_result import BaseOperationResult


class GroupOperationResult(BaseOperationResult):
    """GroupOperationResult.

    :param errors: List of error codes paired with their corresponding error messages
    :type errors: list of { key: int; value: str }
    :param is_success: Success status of the operation
    :type is_success: bool
    :param group_id: Identifier of the Group being acted upon
    :type group_id: str
    :param result: Result of the Groupentitlement after the operation
    :type result: :class:`GroupEntitlement <member-entitlement-management.v4_0.models.GroupEntitlement>`
    """

    _attribute_map = {
        'errors': {'key': 'errors', 'type': '[{ key: int; value: str }]'},
        'is_success': {'key': 'isSuccess', 'type': 'bool'},
        'group_id': {'key': 'groupId', 'type': 'str'},
        'result': {'key': 'result', 'type': 'GroupEntitlement'}
    }

    def __init__(self, errors=None, is_success=None, group_id=None, result=None):
        super(GroupOperationResult, self).__init__(errors=errors, is_success=is_success)
        self.group_id = group_id
        self.result = result
