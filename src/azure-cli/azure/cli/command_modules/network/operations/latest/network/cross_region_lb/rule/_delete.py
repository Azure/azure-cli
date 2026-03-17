# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.rule._delete import Delete as _LBRuleDelete


@register_command("network cross-region-lb rule delete")
class CrossRegionLoadBalancerRuleDelete(_LBRuleDelete):
    """Delete a load balancing rule.

    :example: Delete a load balancing rule.
        az network cross-region-lb rule delete -g MyResourceGroup --lb-name MyLb -n MyLbRule
    """
