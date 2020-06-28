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

    :param disabled_count: Amount that is disabled (Usually from licenses that were provisioned, but became invalid due to loss of subscription in a new billing cycle)
    :type disabled_count: int
    :param license:
    :type license: :class:`AccountUserLicense <licensing.v4_1.models.AccountUserLicense>`
    :param pending_provisioned_count: Amount that will be purchased in the next billing cycle
    :type pending_provisioned_count: int
    :param provisioned_count: Amount that has been purchased
    :type provisioned_count: int
    :param used_count: Amount currently being used.
    :type used_count: int
    """

    _attribute_map = {
        'disabled_count': {'key': 'disabledCount', 'type': 'int'},
        'license': {'key': 'license', 'type': 'AccountUserLicense'},
        'pending_provisioned_count': {'key': 'pendingProvisionedCount', 'type': 'int'},
        'provisioned_count': {'key': 'provisionedCount', 'type': 'int'},
        'used_count': {'key': 'usedCount', 'type': 'int'}
    }

    def __init__(self, disabled_count=None, license=None, pending_provisioned_count=None, provisioned_count=None, used_count=None):
        super(AccountLicenseUsage, self).__init__()
        self.disabled_count = disabled_count
        self.license = license
        self.pending_provisioned_count = pending_provisioned_count
        self.provisioned_count = provisioned_count
        self.used_count = used_count
