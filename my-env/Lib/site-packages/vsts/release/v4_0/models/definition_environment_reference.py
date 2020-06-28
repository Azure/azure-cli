# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DefinitionEnvironmentReference(Model):
    """DefinitionEnvironmentReference.

    :param definition_environment_id:
    :type definition_environment_id: int
    :param definition_environment_name:
    :type definition_environment_name: str
    :param release_definition_id:
    :type release_definition_id: int
    :param release_definition_name:
    :type release_definition_name: str
    """

    _attribute_map = {
        'definition_environment_id': {'key': 'definitionEnvironmentId', 'type': 'int'},
        'definition_environment_name': {'key': 'definitionEnvironmentName', 'type': 'str'},
        'release_definition_id': {'key': 'releaseDefinitionId', 'type': 'int'},
        'release_definition_name': {'key': 'releaseDefinitionName', 'type': 'str'}
    }

    def __init__(self, definition_environment_id=None, definition_environment_name=None, release_definition_id=None, release_definition_name=None):
        super(DefinitionEnvironmentReference, self).__init__()
        self.definition_environment_id = definition_environment_id
        self.definition_environment_name = definition_environment_name
        self.release_definition_id = release_definition_id
        self.release_definition_name = release_definition_name
