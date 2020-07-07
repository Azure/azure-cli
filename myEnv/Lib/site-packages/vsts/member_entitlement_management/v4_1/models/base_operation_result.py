# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BaseOperationResult(Model):
    """BaseOperationResult.

    :param errors: List of error codes paired with their corresponding error messages
    :type errors: list of { key: int; value: str }
    :param is_success: Success status of the operation
    :type is_success: bool
    """

    _attribute_map = {
        'errors': {'key': 'errors', 'type': '[{ key: int; value: str }]'},
        'is_success': {'key': 'isSuccess', 'type': 'bool'}
    }

    def __init__(self, errors=None, is_success=None):
        super(BaseOperationResult, self).__init__()
        self.errors = errors
        self.is_success = is_success
