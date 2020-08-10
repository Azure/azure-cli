# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PackageVersionChange(Model):
    """PackageVersionChange.

    :param change_type:
    :type change_type: object
    :param continuation_token:
    :type continuation_token: long
    :param package_version:
    :type package_version: :class:`PackageVersion <packaging.v4_1.models.PackageVersion>`
    """

    _attribute_map = {
        'change_type': {'key': 'changeType', 'type': 'object'},
        'continuation_token': {'key': 'continuationToken', 'type': 'long'},
        'package_version': {'key': 'packageVersion', 'type': 'PackageVersion'}
    }

    def __init__(self, change_type=None, continuation_token=None, package_version=None):
        super(PackageVersionChange, self).__init__()
        self.change_type = change_type
        self.continuation_token = continuation_token
        self.package_version = package_version
