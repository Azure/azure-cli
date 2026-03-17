# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import AAZResourceIdArgFormat, has_value, AAZStrArg, AAZArgEnum
from azure.cli.command_modules.network.aaz.latest.network.lb.frontend_ip._update import Update as _LBFrontendIPUpdate


class LBFrontendIPUpdate(_LBFrontendIPUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            arg_group="Properties",
            options=['--vnet-name'],
            help="The virtual network (VNet) associated with the subnet (Omit if supplying a subnet id)."
        )
        args_schema.subnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{}",
        )
        args_schema.public_ip_prefix._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIpPrefixes/{}",
        )
        args_schema.public_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{}",
        )
        args_schema.gateway_lb._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}"
        )

        args_schema.zones.Element.enum = AAZArgEnum({
            "1": "1",
            "2": "2",
            "3": "3",
        })
        args_schema.private_ip_allocation_method._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.private_ip_address):
            # update private_ip_address
            if args.private_ip_address:
                args.private_ip_allocation_method = 'Static'
            else:
                # set private_ip_address as null value
                args.private_ip_allocation_method = 'Dynamic'

    def post_instance_update(self, instance):
        if not has_value(instance.properties.subnet.id):
            instance.properties.subnet = None
        if not has_value(instance.properties.public_ip_address.id):
            instance.properties.public_ip_address = None
        if not has_value(instance.properties.public_ip_prefix.id):
            instance.properties.public_ip_prefix = None
        if not has_value(instance.properties.gateway_load_balancer.id):
            instance.properties.gateway_load_balancer = None
