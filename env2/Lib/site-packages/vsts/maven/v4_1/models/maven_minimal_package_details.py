# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MavenMinimalPackageDetails(Model):
    """MavenMinimalPackageDetails.

    :param artifact: Package artifact ID
    :type artifact: str
    :param group: Package group ID
    :type group: str
    :param version: Package version
    :type version: str
    """

    _attribute_map = {
        'artifact': {'key': 'artifact', 'type': 'str'},
        'group': {'key': 'group', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, artifact=None, group=None, version=None):
        super(MavenMinimalPackageDetails, self).__init__()
        self.artifact = artifact
        self.group = group
        self.version = version
