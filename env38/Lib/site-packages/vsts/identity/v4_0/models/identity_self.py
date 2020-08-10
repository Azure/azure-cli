# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class IdentitySelf(Model):
    """IdentitySelf.

    :param account_name:
    :type account_name: str
    :param display_name:
    :type display_name: str
    :param id:
    :type id: str
    :param tenants:
    :type tenants: list of :class:`TenantInfo <identities.v4_0.models.TenantInfo>`
    """

    _attribute_map = {
        'account_name': {'key': 'accountName', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'tenants': {'key': 'tenants', 'type': '[TenantInfo]'}
    }

    def __init__(self, account_name=None, display_name=None, id=None, tenants=None):
        super(IdentitySelf, self).__init__()
        self.account_name = account_name
        self.display_name = display_name
        self.id = id
        self.tenants = tenants
