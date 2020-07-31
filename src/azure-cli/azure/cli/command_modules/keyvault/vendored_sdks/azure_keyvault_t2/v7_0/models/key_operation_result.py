# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class KeyOperationResult(Model):
    """The key operation result.

    Variables are only populated by the server, and will be ignored when
    sending a request.

    :ivar kid: Key identifier
    :vartype kid: str
    :ivar result:
    :vartype result: bytes
    """

    _validation = {
        'kid': {'readonly': True},
        'result': {'readonly': True},
    }

    _attribute_map = {
        'kid': {'key': 'kid', 'type': 'str'},
        'result': {'key': 'value', 'type': 'base64'},
    }

    def __init__(self, **kwargs):
        super(KeyOperationResult, self).__init__(**kwargs)
        self.kid = None
        self.result = None
