# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionLicenseData(Model):
    """ExtensionLicenseData.

    :param created_date:
    :type created_date: datetime
    :param extension_id:
    :type extension_id: str
    :param is_free:
    :type is_free: bool
    :param minimum_required_access_level:
    :type minimum_required_access_level: object
    :param updated_date:
    :type updated_date: datetime
    """

    _attribute_map = {
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'extension_id': {'key': 'extensionId', 'type': 'str'},
        'is_free': {'key': 'isFree', 'type': 'bool'},
        'minimum_required_access_level': {'key': 'minimumRequiredAccessLevel', 'type': 'object'},
        'updated_date': {'key': 'updatedDate', 'type': 'iso-8601'}
    }

    def __init__(self, created_date=None, extension_id=None, is_free=None, minimum_required_access_level=None, updated_date=None):
        super(ExtensionLicenseData, self).__init__()
        self.created_date = created_date
        self.extension_id = extension_id
        self.is_free = is_free
        self.minimum_required_access_level = minimum_required_access_level
        self.updated_date = updated_date
