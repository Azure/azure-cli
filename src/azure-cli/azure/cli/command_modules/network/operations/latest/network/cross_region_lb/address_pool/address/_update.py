# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command, AAZResourceIdArgFormat
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool.address._update import Update as _LBAddressPoolAddressUpdate


@register_command("network cross-region-lb address-pool address update")
class CrossRegionLoadBalancerAddressPoolAddressUpdate(_LBAddressPoolAddressUpdate):
    """Update the backend address into the load balance backend address pool.

    :example: Update the frontend ip of the backend address into the load balance backend address pool.
        az network cross-region-lb address-pool address update -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress --frontend-ip-address /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb2
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}"
        )

        args_schema.frontend_ip_address._nullable = False
        args_schema.ip_address._registered = False
        args_schema.subnet._registered = False
        args_schema.virtual_network._registered = False
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
