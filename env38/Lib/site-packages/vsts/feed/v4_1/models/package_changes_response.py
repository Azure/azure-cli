# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PackageChangesResponse(Model):
    """PackageChangesResponse.

    :param _links:
    :type _links: :class:`ReferenceLinks <packaging.v4_1.models.ReferenceLinks>`
    :param count:
    :type count: int
    :param next_package_continuation_token:
    :type next_package_continuation_token: long
    :param package_changes:
    :type package_changes: list of :class:`PackageChange <packaging.v4_1.models.PackageChange>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'count': {'key': 'count', 'type': 'int'},
        'next_package_continuation_token': {'key': 'nextPackageContinuationToken', 'type': 'long'},
        'package_changes': {'key': 'packageChanges', 'type': '[PackageChange]'}
    }

    def __init__(self, _links=None, count=None, next_package_continuation_token=None, package_changes=None):
        super(PackageChangesResponse, self).__init__()
        self._links = _links
        self.count = count
        self.next_package_continuation_token = next_package_continuation_token
        self.package_changes = package_changes
