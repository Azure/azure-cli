# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool._list import List as _LBAddressPoolList


@register_command("network cross-region-lb address-pool list")
class CrossRegionLoadBalancerAddressPoolList(_LBAddressPoolList):
    """List all the load balancer backed address pools.

    :example: List address pools.
        az network cross-region-lb address-pool list -g MyResourceGroup --lb-name MyLb -o table
    """
