# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model

class ValidateAccountName(Model):
    _attribute_map = {
        'valid': {'key': 'valid', 'type': 'bool'},
        'message': {'key': 'message', 'type': 'str'},
    }

    def __init__(self, valid=None, message=None):
        self.valid = valid
        self.message = message
