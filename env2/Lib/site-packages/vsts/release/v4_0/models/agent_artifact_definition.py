# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AgentArtifactDefinition(Model):
    """AgentArtifactDefinition.

    :param alias:
    :type alias: str
    :param artifact_type:
    :type artifact_type: object
    :param details:
    :type details: str
    :param name:
    :type name: str
    :param version:
    :type version: str
    """

    _attribute_map = {
        'alias': {'key': 'alias', 'type': 'str'},
        'artifact_type': {'key': 'artifactType', 'type': 'object'},
        'details': {'key': 'details', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, alias=None, artifact_type=None, details=None, name=None, version=None):
        super(AgentArtifactDefinition, self).__init__()
        self.alias = alias
        self.artifact_type = artifact_type
        self.details = details
        self.name = name
        self.version = version
