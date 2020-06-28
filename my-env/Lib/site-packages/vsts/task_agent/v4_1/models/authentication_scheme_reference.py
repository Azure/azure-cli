# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AuthenticationSchemeReference(Model):
    """AuthenticationSchemeReference.

    :param inputs:
    :type inputs: dict
    :param type:
    :type type: str
    """

    _attribute_map = {
        'inputs': {'key': 'inputs', 'type': '{str}'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, inputs=None, type=None):
        super(AuthenticationSchemeReference, self).__init__()
        self.inputs = inputs
        self.type = type
