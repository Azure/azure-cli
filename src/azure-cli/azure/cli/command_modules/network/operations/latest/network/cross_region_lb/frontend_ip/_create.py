# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command, AAZResourceIdArgFormat, AAZArgEnum
from azure.cli.command_modules.network.aaz.latest.network.lb.frontend_ip._create import Create as _LBFrontendIPCreate


@register_command("network cross-region-lb frontend-ip create")
class CrossRegionLoadBalancerFrontendIPCreate(_LBFrontendIPCreate):
    """Create a frontend IP address.

    :example: Create a frontend ip address for a public load balancer.
        az network cross-region-lb frontend-ip create -g MyResourceGroup --lb-name MyLb -n MyFrontendIp --public-ip-address MyFrontendIp
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_prefix._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIpPrefixes/{}",
        )
        args_schema.public_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{}",
        )
        args_schema.zones.Element.enum = AAZArgEnum({
            "1": "1",
            "2": "2",
            "3": "3",
        })

        args_schema.private_ip_address._registered = False
        args_schema.private_ip_address_version._registered = False
        args_schema.private_ip_allocation_method._registered = False
        args_schema.subnet._registered = False
        args_schema.gateway_lb._registered = False
        return args_schema
