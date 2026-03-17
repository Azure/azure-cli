# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb._list import List as _LBList


@register_command("network cross-region-lb list")
class CrossRegionLoadBalancerList(_LBList):
    """List load balancers.

    :example: List load balancers.
        az network cross-region-lb list -g MyResourceGroup
    """
