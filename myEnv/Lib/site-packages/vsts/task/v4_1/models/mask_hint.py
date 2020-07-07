# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MaskHint(Model):
    """MaskHint.

    :param type:
    :type type: object
    :param value:
    :type value: str
    """

    _attribute_map = {
        'type': {'key': 'type', 'type': 'object'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, type=None, value=None):
        super(MaskHint, self).__init__()
        self.type = type
        self.value = value
