# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.public_ip._list import List as _PublicIPList


_PUBLIC_IP_SHOW_TABLE_TRANSFORM = (
    '{Name:name, ResourceGroup:resourceGroup, Location:location, '
    'Zones: (!zones && \' \') || join(` `, zones), '
    'Address:ipAddress, AddressVersion:publicIpAddressVersion, '
    'AllocationMethod:publicIpAllocationMethod, '
    'IdleTimeoutInMinutes:idleTimeoutInMinutes, '
    'ProvisioningState:provisioningState}'
)


class PublicIPList(_PublicIPList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_transformer = '[].' + _PUBLIC_IP_SHOW_TABLE_TRANSFORM
