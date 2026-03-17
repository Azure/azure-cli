# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command, AAZResourceIdArgFormat, has_value, AAZStrArg
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool._update import Update as _LBAddressPoolUpdate


@register_command("network cross-region-lb address-pool update")
class CrossRegionLoadBalancerAddressPoolUpdate(_LBAddressPoolUpdate):
    """Update a load balancer backend address pool.

    :example: Update all backend addresses in the address pool using shorthand syntax
        az network cross-region-lb address-pool update -g MyResourceGroup --lb-name MyLb -n MyAddressPool --backend-addresses "[{name:addr1,frontend-ip-address:'/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb1'},{name:addr2,frontend-ip-address:'/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb2'}]"

    :example: Update the frontend-ip-address of the first backend address in the address pool using shorthand syntax
        az network cross-region-lb address-pool update -g MyResourceGroup --lb-name MyLb -n MyAddressPool --backend-addresses [0].frontend-ip-address=/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb1

    :example: Remove the first backend address in the address pool using shorthand syntax
        az network cross-region-lb address-pool update -g MyResourceGroup --lb-name MyLb -n MyAddressPool --backend-addresses [0]=null
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.admin_state = AAZStrArg(
            options=["--admin-state"],
            arg_group="Properties",
            help="Default administrative state to backend addresses in `--backend-addresses`.",
        )
        args_schema.admin_state.enum = args_schema.backend_addresses.Element.admin_state.enum
        # not support name, the frontend id should belong to a regional load balance
        args_schema.backend_addresses.Element.frontend_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}"
        )
        args_schema.backend_addresses.Element.name._nullable = False
        args_schema.backend_addresses.Element.frontend_ip_address._nullable = False
        args_schema.backend_addresses.Element.admin_state._nullable = False

        args_schema.tunnel_interfaces._registered = False
        args_schema.backend_addresses.Element.ip_address._registered = False
        args_schema.backend_addresses.Element.subnet._registered = False
        args_schema.backend_addresses.Element.virtual_network._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.backend_addresses):
            for backend_address in args.backend_addresses:
                if not has_value(backend_address.admin_state) and has_value(args.admin_state):
                    # use the command level argument --admin-state
                    backend_address.admin_state = args.admin_state
