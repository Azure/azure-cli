# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TenantInfo(Model):
    """TenantInfo.

    :param home_tenant:
    :type home_tenant: bool
    :param tenant_id:
    :type tenant_id: str
    :param tenant_name:
    :type tenant_name: str
    """

    _attribute_map = {
        'home_tenant': {'key': 'homeTenant', 'type': 'bool'},
        'tenant_id': {'key': 'tenantId', 'type': 'str'},
        'tenant_name': {'key': 'tenantName', 'type': 'str'}
    }

    def __init__(self, home_tenant=None, tenant_id=None, tenant_name=None):
        super(TenantInfo, self).__init__()
        self.home_tenant = home_tenant
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
