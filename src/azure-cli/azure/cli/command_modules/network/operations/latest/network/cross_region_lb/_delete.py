# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb._delete import Delete as _LBDelete


@register_command("network cross-region-lb delete")
class CrossRegionLoadBalancerDelete(_LBDelete):
    """Delete the specified load balancer.

    :example: Delete a load balancer.
        az network cross-region-lb delete -g MyResourceGroup -n MyLb
    """
