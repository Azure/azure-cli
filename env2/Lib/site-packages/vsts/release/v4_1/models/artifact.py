# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Artifact(Model):
    """Artifact.

    :param alias: Gets or sets alias.
    :type alias: str
    :param definition_reference: Gets or sets definition reference. e.g. {"project":{"id":"fed755ea-49c5-4399-acea-fd5b5aa90a6c","name":"myProject"},"definition":{"id":"1","name":"mybuildDefinition"},"connection":{"id":"1","name":"myConnection"}}
    :type definition_reference: dict
    :param is_primary: Gets or sets as artifact is primary or not.
    :type is_primary: bool
    :param source_id:
    :type source_id: str
    :param type: Gets or sets type. It can have value as 'Build', 'Jenkins', 'GitHub', 'Nuget', 'Team Build (external)', 'ExternalTFSBuild', 'Git', 'TFVC', 'ExternalTfsXamlBuild'.
    :type type: str
    """

    _attribute_map = {
        'alias': {'key': 'alias', 'type': 'str'},
        'definition_reference': {'key': 'definitionReference', 'type': '{ArtifactSourceReference}'},
        'is_primary': {'key': 'isPrimary', 'type': 'bool'},
        'source_id': {'key': 'sourceId', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, alias=None, definition_reference=None, is_primary=None, source_id=None, type=None):
        super(Artifact, self).__init__()
        self.alias = alias
        self.definition_reference = definition_reference
        self.is_primary = is_primary
        self.source_id = source_id
        self.type = type
