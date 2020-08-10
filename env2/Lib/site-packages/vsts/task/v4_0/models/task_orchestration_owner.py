# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskOrchestrationOwner(Model):
    """TaskOrchestrationOwner.

    :param _links:
    :type _links: :class:`ReferenceLinks <task.v4_0.models.ReferenceLinks>`
    :param id:
    :type id: int
    :param name:
    :type name: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, _links=None, id=None, name=None):
        super(TaskOrchestrationOwner, self).__init__()
        self._links = _links
        self.id = id
        self.name = name
