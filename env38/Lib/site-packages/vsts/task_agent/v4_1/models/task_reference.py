# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskReference(Model):
    """TaskReference.

    :param id:
    :type id: str
    :param inputs:
    :type inputs: dict
    :param name:
    :type name: str
    :param version:
    :type version: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'inputs': {'key': 'inputs', 'type': '{str}'},
        'name': {'key': 'name', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, id=None, inputs=None, name=None, version=None):
        super(TaskReference, self).__init__()
        self.id = id
        self.inputs = inputs
        self.name = name
        self.version = version
