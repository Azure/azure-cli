# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb._show import Show as _LBShow


@register_command("network cross-region-lb show")
class CrossRegionLoadBalancerShow(_LBShow):
    """Get the details of a load balancer.

    :example: Get the details of a load balancer.
        az network cross-region-lb show -g MyResourceGroup -n MyLb
    """
