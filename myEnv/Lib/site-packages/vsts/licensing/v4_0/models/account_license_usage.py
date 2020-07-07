# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountLicenseUsage(Model):
    """AccountLicenseUsage.

    :param license:
    :type license: :class:`AccountUserLicense <licensing.v4_0.models.AccountUserLicense>`
    :param provisioned_count:
    :type provisioned_count: int
    :param used_count:
    :type used_count: int
    """

    _attribute_map = {
        'license': {'key': 'license', 'type': 'AccountUserLicense'},
        'provisioned_count': {'key': 'provisionedCount', 'type': 'int'},
        'used_count': {'key': 'usedCount', 'type': 'int'}
    }

    def __init__(self, license=None, provisioned_count=None, used_count=None):
        super(AccountLicenseUsage, self).__init__()
        self.license = license
        self.provisioned_count = provisioned_count
        self.used_count = used_count
