# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .maven_pom_gav import MavenPomGav


class Plugin(MavenPomGav):
    """Plugin.

    :param artifact_id:
    :type artifact_id: str
    :param group_id:
    :type group_id: str
    :param version:
    :type version: str
    :param configuration:
    :type configuration: :class:`PluginConfiguration <maven.v4_1.models.PluginConfiguration>`
    """

    _attribute_map = {
        'artifact_id': {'key': 'artifactId', 'type': 'str'},
        'group_id': {'key': 'groupId', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'},
        'configuration': {'key': 'configuration', 'type': 'PluginConfiguration'}
    }

    def __init__(self, artifact_id=None, group_id=None, version=None, configuration=None):
        super(Plugin, self).__init__(artifact_id=artifact_id, group_id=group_id, version=version)
        self.configuration = configuration
