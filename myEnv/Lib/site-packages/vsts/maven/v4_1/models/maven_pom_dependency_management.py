# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MavenPomDependencyManagement(Model):
    """MavenPomDependencyManagement.

    :param dependencies:
    :type dependencies: list of :class:`MavenPomDependency <maven.v4_1.models.MavenPomDependency>`
    """

    _attribute_map = {
        'dependencies': {'key': 'dependencies', 'type': '[MavenPomDependency]'}
    }

    def __init__(self, dependencies=None):
        super(MavenPomDependencyManagement, self).__init__()
        self.dependencies = dependencies
