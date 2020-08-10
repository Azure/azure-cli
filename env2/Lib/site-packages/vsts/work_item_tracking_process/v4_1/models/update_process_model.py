# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UpdateProcessModel(Model):
    """UpdateProcessModel.

    :param description:
    :type description: str
    :param is_default:
    :type is_default: bool
    :param is_enabled:
    :type is_enabled: bool
    :param name:
    :type name: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'is_default': {'key': 'isDefault', 'type': 'bool'},
        'is_enabled': {'key': 'isEnabled', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, description=None, is_default=None, is_enabled=None, name=None):
        super(UpdateProcessModel, self).__init__()
        self.description = description
        self.is_default = is_default
        self.is_enabled = is_enabled
        self.name = name
