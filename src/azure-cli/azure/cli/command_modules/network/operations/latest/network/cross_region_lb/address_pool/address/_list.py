# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool.address._list import List as _LBAddressPoolAddressList


@register_command("network cross-region-lb address-pool address list")
class CrossRegionLoadBalancerAddressPoolAddressList(_LBAddressPoolAddressList):
    """List all backend addresses of the load balance backend address pool.

    :example: List all backend addresses of the load balance backend address pool.
        az network cross-region-lb address-pool address list -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool
    """
