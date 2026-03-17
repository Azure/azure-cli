# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool.address._remove import Remove as _LBAddressPoolAddressRemove


@register_command("network cross-region-lb address-pool address remove")
class CrossRegionLoadBalancerAddressPoolAddressRemove(_LBAddressPoolAddressRemove):
    """Remove one backend address from the load balance backend address pool.
    :example: Remove one backend address from the load balance backend address pool.
        az network cross-region-lb address-pool address remove -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress
    """
