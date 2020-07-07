# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Metric(Model):
    """Metric.

    :param name:
    :type name: str
    :param value:
    :type value: int
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'value': {'key': 'value', 'type': 'int'}
    }

    def __init__(self, name=None, value=None):
        super(Metric, self).__init__()
        self.name = name
        self.value = value
