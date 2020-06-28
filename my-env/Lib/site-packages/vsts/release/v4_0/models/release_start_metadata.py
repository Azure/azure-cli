# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseStartMetadata(Model):
    """ReleaseStartMetadata.

    :param artifacts: Sets list of artifact to create a release.
    :type artifacts: list of :class:`ArtifactMetadata <release.v4_0.models.ArtifactMetadata>`
    :param definition_id: Sets definition Id to create a release.
    :type definition_id: int
    :param description: Sets description to create a release.
    :type description: str
    :param is_draft: Sets 'true' to create release in draft mode, 'false' otherwise.
    :type is_draft: bool
    :param manual_environments: Sets list of environments to manual as condition.
    :type manual_environments: list of str
    :param properties:
    :type properties: :class:`object <release.v4_0.models.object>`
    :param reason: Sets reason to create a release.
    :type reason: object
    """

    _attribute_map = {
        'artifacts': {'key': 'artifacts', 'type': '[ArtifactMetadata]'},
        'definition_id': {'key': 'definitionId', 'type': 'int'},
        'description': {'key': 'description', 'type': 'str'},
        'is_draft': {'key': 'isDraft', 'type': 'bool'},
        'manual_environments': {'key': 'manualEnvironments', 'type': '[str]'},
        'properties': {'key': 'properties', 'type': 'object'},
        'reason': {'key': 'reason', 'type': 'object'}
    }

    def __init__(self, artifacts=None, definition_id=None, description=None, is_draft=None, manual_environments=None, properties=None, reason=None):
        super(ReleaseStartMetadata, self).__init__()
        self.artifacts = artifacts
        self.definition_id = definition_id
        self.description = description
        self.is_draft = is_draft
        self.manual_environments = manual_environments
        self.properties = properties
        self.reason = reason
