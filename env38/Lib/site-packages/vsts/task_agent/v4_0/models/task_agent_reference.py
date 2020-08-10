# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentReference(Model):
    """TaskAgentReference.

    :param _links:
    :type _links: :class:`ReferenceLinks <task-agent.v4_0.models.ReferenceLinks>`
    :param enabled: Gets or sets a value indicating whether or not this agent should be enabled for job execution.
    :type enabled: bool
    :param id: Gets the identifier of the agent.
    :type id: int
    :param name: Gets the name of the agent.
    :type name: str
    :param status: Gets the current connectivity status of the agent.
    :type status: object
    :param version: Gets the version of the agent.
    :type version: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'enabled': {'key': 'enabled', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, _links=None, enabled=None, id=None, name=None, status=None, version=None):
        super(TaskAgentReference, self).__init__()
        self._links = _links
        self.enabled = enabled
        self.id = id
        self.name = name
        self.status = status
        self.version = version
