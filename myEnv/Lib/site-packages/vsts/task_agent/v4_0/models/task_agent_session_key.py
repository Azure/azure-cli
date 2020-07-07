# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentSessionKey(Model):
    """TaskAgentSessionKey.

    :param encrypted: Gets or sets a value indicating whether or not the key value is encrypted. If this value is true, the Value property should be decrypted using the <c>RSA</c> key exchanged with the server during registration.
    :type encrypted: bool
    :param value: Gets or sets the symmetric key value.
    :type value: str
    """

    _attribute_map = {
        'encrypted': {'key': 'encrypted', 'type': 'bool'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, encrypted=None, value=None):
        super(TaskAgentSessionKey, self).__init__()
        self.encrypted = encrypted
        self.value = value
