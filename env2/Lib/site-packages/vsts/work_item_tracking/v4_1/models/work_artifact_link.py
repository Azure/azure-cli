# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkArtifactLink(Model):
    """WorkArtifactLink.

    :param artifact_type: Target artifact type.
    :type artifact_type: str
    :param link_type: Outbound link type.
    :type link_type: str
    :param tool_type: Target tool type.
    :type tool_type: str
    """

    _attribute_map = {
        'artifact_type': {'key': 'artifactType', 'type': 'str'},
        'link_type': {'key': 'linkType', 'type': 'str'},
        'tool_type': {'key': 'toolType', 'type': 'str'}
    }

    def __init__(self, artifact_type=None, link_type=None, tool_type=None):
        super(WorkArtifactLink, self).__init__()
        self.artifact_type = artifact_type
        self.link_type = link_type
        self.tool_type = tool_type
