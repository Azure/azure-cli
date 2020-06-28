# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ArtifactUriQueryResult(Model):
    """ArtifactUriQueryResult.

    :param artifact_uris_query_result:
    :type artifact_uris_query_result: dict
    """

    _attribute_map = {
        'artifact_uris_query_result': {'key': 'artifactUrisQueryResult', 'type': '{[WorkItemReference]}'}
    }

    def __init__(self, artifact_uris_query_result=None):
        super(ArtifactUriQueryResult, self).__init__()
        self.artifact_uris_query_result = artifact_uris_query_result
