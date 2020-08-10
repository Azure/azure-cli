# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NpmPackageVersionDeletionState(Model):
    """NpmPackageVersionDeletionState.

    :param name:
    :type name: str
    :param unpublished_date:
    :type unpublished_date: datetime
    :param version:
    :type version: str
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'unpublished_date': {'key': 'unpublishedDate', 'type': 'iso-8601'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, name=None, unpublished_date=None, version=None):
        super(NpmPackageVersionDeletionState, self).__init__()
        self.name = name
        self.unpublished_date = unpublished_date
        self.version = version
