# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.frontend_ip._list import List as _LBFrontendIPList


@register_command("network cross-region-lb frontend-ip list")
class CrossRegionLoadBalancerFrontendIPList(_LBFrontendIPList):
    """List frontend IP addresses.

    :example: List frontend IP addresses.
        az network cross-region-lb frontend-ip list -g MyResourceGroup --lb-name MyLb
    """
