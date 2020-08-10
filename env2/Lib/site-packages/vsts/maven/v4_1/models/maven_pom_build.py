# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MavenPomBuild(Model):
    """MavenPomBuild.

    :param plugins:
    :type plugins: list of :class:`Plugin <maven.v4_1.models.Plugin>`
    """

    _attribute_map = {
        'plugins': {'key': 'plugins', 'type': '[Plugin]'}
    }

    def __init__(self, plugins=None):
        super(MavenPomBuild, self).__init__()
        self.plugins = plugins
