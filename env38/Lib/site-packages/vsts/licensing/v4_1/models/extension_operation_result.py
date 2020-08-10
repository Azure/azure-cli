# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionOperationResult(Model):
    """ExtensionOperationResult.

    :param account_id:
    :type account_id: str
    :param extension_id:
    :type extension_id: str
    :param message:
    :type message: str
    :param operation:
    :type operation: object
    :param result:
    :type result: object
    :param user_id:
    :type user_id: str
    """

    _attribute_map = {
        'account_id': {'key': 'accountId', 'type': 'str'},
        'extension_id': {'key': 'extensionId', 'type': 'str'},
        'message': {'key': 'message', 'type': 'str'},
        'operation': {'key': 'operation', 'type': 'object'},
        'result': {'key': 'result', 'type': 'object'},
        'user_id': {'key': 'userId', 'type': 'str'}
    }

    def __init__(self, account_id=None, extension_id=None, message=None, operation=None, result=None, user_id=None):
        super(ExtensionOperationResult, self).__init__()
        self.account_id = account_id
        self.extension_id = extension_id
        self.message = message
        self.operation = operation
        self.result = result
        self.user_id = user_id
