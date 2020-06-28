# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DependencyBinding(Model):
    """DependencyBinding.

    :param key:
    :type key: str
    :param value:
    :type value: str
    """

    _attribute_map = {
        'key': {'key': 'key', 'type': 'str'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, key=None, value=None):
        super(DependencyBinding, self).__init__()
        self.key = key
        self.value = value
