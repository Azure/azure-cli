# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PackageChange(Model):
    """PackageChange.

    :param package:
    :type package: :class:`Package <packaging.v4_1.models.Package>`
    :param package_version_change:
    :type package_version_change: :class:`PackageVersionChange <packaging.v4_1.models.PackageVersionChange>`
    """

    _attribute_map = {
        'package': {'key': 'package', 'type': 'Package'},
        'package_version_change': {'key': 'packageVersionChange', 'type': 'PackageVersionChange'}
    }

    def __init__(self, package=None, package_version_change=None):
        super(PackageChange, self).__init__()
        self.package = package
        self.package_version_change = package_version_change
