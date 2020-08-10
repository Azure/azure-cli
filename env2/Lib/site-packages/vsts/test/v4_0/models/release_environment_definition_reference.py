# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseEnvironmentDefinitionReference(Model):
    """ReleaseEnvironmentDefinitionReference.

    :param definition_id:
    :type definition_id: int
    :param environment_definition_id:
    :type environment_definition_id: int
    """

    _attribute_map = {
        'definition_id': {'key': 'definitionId', 'type': 'int'},
        'environment_definition_id': {'key': 'environmentDefinitionId', 'type': 'int'}
    }

    def __init__(self, definition_id=None, environment_definition_id=None):
        super(ReleaseEnvironmentDefinitionReference, self).__init__()
        self.definition_id = definition_id
        self.environment_definition_id = environment_definition_id
