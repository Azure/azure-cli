# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.vpn_connection._wait import Wait as _VpnConnectionWait


@register_command("network vpn-connection packet-capture wait")
class VpnConnectionPacketCaptureWait(_VpnConnectionWait):
    """Place the CLI in a waiting state until a condition of the VPN connection is met.

    :example: Pause executing next line of CLI script until the VPN connection is successfully provisioned.
        az network vpn-connection packet-capture wait -g MyResourceGroup -n MyConnection --created
    """
