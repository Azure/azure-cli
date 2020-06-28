# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestMethod(Model):
    """TestMethod.

    :param container:
    :type container: str
    :param name:
    :type name: str
    """

    _attribute_map = {
        'container': {'key': 'container', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, container=None, name=None):
        super(TestMethod, self).__init__()
        self.container = container
        self.name = name
