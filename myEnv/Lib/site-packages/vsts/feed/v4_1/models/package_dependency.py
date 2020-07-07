# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PackageDependency(Model):
    """PackageDependency.

    :param group:
    :type group: str
    :param package_name:
    :type package_name: str
    :param version_range:
    :type version_range: str
    """

    _attribute_map = {
        'group': {'key': 'group', 'type': 'str'},
        'package_name': {'key': 'packageName', 'type': 'str'},
        'version_range': {'key': 'versionRange', 'type': 'str'}
    }

    def __init__(self, group=None, package_name=None, version_range=None):
        super(PackageDependency, self).__init__()
        self.group = group
        self.package_name = package_name
        self.version_range = version_range
