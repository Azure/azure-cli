# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountEntitlementUpdateModel(Model):
    """AccountEntitlementUpdateModel.

    :param license: Gets or sets the license for the entitlement
    :type license: :class:`License <licensing.v4_0.models.License>`
    """

    _attribute_map = {
        'license': {'key': 'license', 'type': 'License'}
    }

    def __init__(self, license=None):
        super(AccountEntitlementUpdateModel, self).__init__()
        self.license = license
