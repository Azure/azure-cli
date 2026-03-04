# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.core.util import CLIError
from azure.cli.command_modules.network.aaz.latest.network.private_link_service._create import Create as _PrivateLinkServiceCreate


class PrivateLinkServiceCreate(_PrivateLinkServiceCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(options=['--vnet-name'], arg_group="IP Configuration", help="The virtual network (VNet) name.")
        args_schema.subnet = AAZResourceIdArg(
            options=['--subnet'],
            arg_group="IP Configuration",
            help="Name or ID of subnet to use. If name provided, also supply `--vnet-name`.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{}"
            )
        )
        args_schema.private_ip_address = AAZStrArg(options=['--private-ip-address'], arg_group="IP Configuration", help="Static private IP address to use.")
        args_schema.private_ip_address_version = AAZStrArg(options=['--private-ip-address-version'], arg_group="IP Configuration", help="IP version of the private IP address.",
                                                           default="IPv4", enum={"IPv4": "IPv4", "IPv6": "IPv6"})
        args_schema.private_ip_allocation_method = AAZStrArg(options=['--private-ip-allocation-method'], arg_group="IP Configuration", help="Private IP address allocation method.",
                                                             enum={"Dynamic": "Dynamic", "Static": "Static"})
        args_schema.lb_name = AAZStrArg(options=['--lb-name'], help="Name of the load balancer to retrieve frontend IP configs from. Ignored if a frontend IP configuration ID is supplied.")
        args_schema.lb_frontend_ip_configs = AAZListArg(options=['--lb-frontend-ip-configs'], help="Space-separated list of names or IDs of load balancer frontend IP configurations to link to. If names are used, also supply `--lb-name`.")
        args_schema.lb_frontend_ip_configs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIpConfigurations/{}"
            )
        )

        args_schema.load_balancer_frontend_ip_configurations._registered = False
        args_schema.edge_zone_type._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if not has_value(args.ip_configurations):
            args.ip_configurations = [{
                'name': '{}_ipconfig_0'.format(args.name.to_serialized_data()),
                'private_ip_address': args.private_ip_address,
                'private_ip_allocation_method': args.private_ip_allocation_method,
                'private_ip_address_version': args.private_ip_address_version,
                'subnet': {'id': args.subnet}
            }]

        args.load_balancer_frontend_ip_configurations = assign_aaz_list_arg(
            args.load_balancer_frontend_ip_configurations,
            args.lb_frontend_ip_configs,
            element_transformer=lambda _, lb_frontend_ip_config: {"id": lb_frontend_ip_config}
        )

        if has_value(args.edge_zone):
            args.edge_zone_type = 'EdgeZone'
        if not has_value(args.lb_frontend_ip_configs) and not has_value(args.destination_ip_address):
            raise CLIError("usage error: either --lb-frontend-ip-configs or --destination-ip-address is required")
