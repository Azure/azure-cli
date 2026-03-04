# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.frontend_ip._delete import Delete as _LBFrontendIPDelete


@register_command("network cross-region-lb frontend-ip delete")
class CrossRegionLoadBalancerFrontendIPDelete(_LBFrontendIPDelete):
    """Delete a frontend IP address.

    :example: Delete a frontend IP address.
        az network cross-region-lb frontend-ip delete -g MyResourceGroup --lb-name MyLb -n MyFrontendIp
    """
