# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .maven_pom_gav import MavenPomGav


class MavenPomDependency(MavenPomGav):
    """MavenPomDependency.

    :param artifact_id:
    :type artifact_id: str
    :param group_id:
    :type group_id: str
    :param version:
    :type version: str
    :param optional:
    :type optional: bool
    :param scope:
    :type scope: str
    :param type:
    :type type: str
    """

    _attribute_map = {
        'artifact_id': {'key': 'artifactId', 'type': 'str'},
        'group_id': {'key': 'groupId', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'},
        'optional': {'key': 'optional', 'type': 'bool'},
        'scope': {'key': 'scope', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, artifact_id=None, group_id=None, version=None, optional=None, scope=None, type=None):
        super(MavenPomDependency, self).__init__(artifact_id=artifact_id, group_id=group_id, version=version)
        self.optional = optional
        self.scope = scope
        self.type = type
