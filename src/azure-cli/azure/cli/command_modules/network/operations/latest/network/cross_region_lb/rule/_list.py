# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.rule._list import List as _LBRuleList


@register_command("network cross-region-lb rule list")
class CrossRegionLoadBalancerRuleList(_LBRuleList):
    """List load balancing rules.

    :example: List load balancing rules.
        az network cross-region-lb rule list -g MyResourceGroup --lb-name MyLb -o table
    """
