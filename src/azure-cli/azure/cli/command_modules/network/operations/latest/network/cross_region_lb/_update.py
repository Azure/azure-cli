# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb._update import Update as _LBUpdate


@register_command("network cross-region-lb update")
class CrossRegionLoadBalancerUpdate(_LBUpdate):
    """Update a load balancer.

    This command can only be used to update the tags for a load balancer.
    Name and resource group are immutable and cannot be updated.

    :example: Update the tags of a load balancer.
        az network cross-region-lb update -g MyResourceGroup -n MyLB --tags CostCenter=MyTestGroup
    """
