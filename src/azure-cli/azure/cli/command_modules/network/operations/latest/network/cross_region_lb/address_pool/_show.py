# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool._show import Show as _LBAddressPoolShow


@register_command("network cross-region-lb address-pool show")
class CrossRegionLoadBalancerAddressPoolShow(_LBAddressPoolShow):
    """Get load balancer backend address pool.

    :example: Get the details of an address pool.
        az network cross-region-lb address-pool show -g MyResourceGroup --lb-name MyLb -n MyAddressPool
    """
