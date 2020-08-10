# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResolutionState(Model):
    """TestResolutionState.

    :param id:
    :type id: int
    :param name:
    :type name: str
    :param project:
    :type project: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'project': {'key': 'project', 'type': 'ShallowReference'}
    }

    def __init__(self, id=None, name=None, project=None):
        super(TestResolutionState, self).__init__()
        self.id = id
        self.name = name
        self.project = project
