# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway._list_bgp_peer_status import \
    ListBgpPeerStatus as _ListBgpPeerStatus
from azure.cli.command_modules.network._format import transform_vnet_gateway_bgp_peer_table


class VNetGatewayListBgpPeerStatus(_ListBgpPeerStatus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_transformer = transform_vnet_gateway_bgp_peer_table
