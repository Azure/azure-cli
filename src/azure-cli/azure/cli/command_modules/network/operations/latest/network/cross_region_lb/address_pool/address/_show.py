# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool.address._show import Show as _LBAddressPoolAddressShow


@register_command("network cross-region-lb address-pool address show")
class CrossRegionLoadBalancerAddressPoolAddressShow(_LBAddressPoolAddressShow):
    """Show the backend address from the load balance backend address pool.

    :example: Show the backend address from the load balance backend address pool.
        az network cross-region-lb address-pool address show -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress
    """
