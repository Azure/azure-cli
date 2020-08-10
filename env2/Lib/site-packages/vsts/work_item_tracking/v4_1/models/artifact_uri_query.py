# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ArtifactUriQuery(Model):
    """ArtifactUriQuery.

    :param artifact_uris: List of artifact URIs to use for querying work items.
    :type artifact_uris: list of str
    """

    _attribute_map = {
        'artifact_uris': {'key': 'artifactUris', 'type': '[str]'}
    }

    def __init__(self, artifact_uris=None):
        super(ArtifactUriQuery, self).__init__()
        self.artifact_uris = artifact_uris
