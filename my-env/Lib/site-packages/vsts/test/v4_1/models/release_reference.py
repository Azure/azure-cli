# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseReference(Model):
    """ReleaseReference.

    :param definition_id:
    :type definition_id: int
    :param environment_definition_id:
    :type environment_definition_id: int
    :param environment_definition_name:
    :type environment_definition_name: str
    :param environment_id:
    :type environment_id: int
    :param environment_name:
    :type environment_name: str
    :param id:
    :type id: int
    :param name:
    :type name: str
    """

    _attribute_map = {
        'definition_id': {'key': 'definitionId', 'type': 'int'},
        'environment_definition_id': {'key': 'environmentDefinitionId', 'type': 'int'},
        'environment_definition_name': {'key': 'environmentDefinitionName', 'type': 'str'},
        'environment_id': {'key': 'environmentId', 'type': 'int'},
        'environment_name': {'key': 'environmentName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, definition_id=None, environment_definition_id=None, environment_definition_name=None, environment_id=None, environment_name=None, id=None, name=None):
        super(ReleaseReference, self).__init__()
        self.definition_id = definition_id
        self.environment_definition_id = environment_definition_id
        self.environment_definition_name = environment_definition_name
        self.environment_id = environment_id
        self.environment_name = environment_name
        self.id = id
        self.name = name
