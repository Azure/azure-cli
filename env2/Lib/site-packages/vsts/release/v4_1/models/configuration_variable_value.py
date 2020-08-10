# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ConfigurationVariableValue(Model):
    """ConfigurationVariableValue.

    :param is_secret: Gets or sets as variable is secret or not.
    :type is_secret: bool
    :param value: Gets or sets value of the configuration variable.
    :type value: str
    """

    _attribute_map = {
        'is_secret': {'key': 'isSecret', 'type': 'bool'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, is_secret=None, value=None):
        super(ConfigurationVariableValue, self).__init__()
        self.is_secret = is_secret
        self.value = value
