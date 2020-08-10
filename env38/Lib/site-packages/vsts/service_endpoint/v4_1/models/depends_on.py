# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DependsOn(Model):
    """DependsOn.

    :param input:
    :type input: str
    :param map:
    :type map: list of :class:`DependencyBinding <service-endpoint.v4_1.models.DependencyBinding>`
    """

    _attribute_map = {
        'input': {'key': 'input', 'type': 'str'},
        'map': {'key': 'map', 'type': '[DependencyBinding]'}
    }

    def __init__(self, input=None, map=None):
        super(DependsOn, self).__init__()
        self.input = input
        self.map = map
