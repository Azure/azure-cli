# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb._wait import Wait as _LBWait


@register_command("network cross-region-lb wait")
class CrossRegionLoadBalancerWait(_LBWait):
    """Place the CLI in a waiting state until a condition of the cross-region load balancer is met.

    :example: Wait for load balancer to return as created.
        az network cross-region-lb wait -g MyResourceGroup -n MyLb --created
    """
