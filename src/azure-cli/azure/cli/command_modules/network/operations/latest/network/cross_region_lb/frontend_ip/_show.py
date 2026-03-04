# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.frontend_ip._show import Show as _LBFrontendIPShow


@register_command("network cross-region-lb frontend-ip show")
class CrossRegionLoadBalancerFrontendIPShow(_LBFrontendIPShow):
    """Get the details of a frontend IP address.

    :example: Get the details of a frontend IP address.
        az network cross-region-lb frontend-ip show -g MyResourceGroup --lb-name MyLb -n MyFrontendIp
    """
