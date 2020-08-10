# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ArtifactVersionQueryResult(Model):
    """ArtifactVersionQueryResult.

    :param artifact_versions:
    :type artifact_versions: list of :class:`ArtifactVersion <release.v4_0.models.ArtifactVersion>`
    """

    _attribute_map = {
        'artifact_versions': {'key': 'artifactVersions', 'type': '[ArtifactVersion]'}
    }

    def __init__(self, artifact_versions=None):
        super(ArtifactVersionQueryResult, self).__init__()
        self.artifact_versions = artifact_versions
