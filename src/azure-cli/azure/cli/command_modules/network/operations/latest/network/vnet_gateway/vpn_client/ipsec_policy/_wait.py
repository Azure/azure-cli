# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway._wait import Wait as _VNetGatewayWait


@register_command("network vnet-gateway vpn-client ipsec-policy wait")
class VNetGatewayVpnClientIpsecPolicyWait(_VNetGatewayWait):
    """Place the CLI in a waiting state until a condition of the virtual network gateway is met.

    :example: Pause executing next line of CLI script until the virtual network gateway is successfully provisioned.
        az network vnet-gateway vpn-client ipsec-policy wait -g MyResourceGroup -n MyVnetGateway --created
    """
