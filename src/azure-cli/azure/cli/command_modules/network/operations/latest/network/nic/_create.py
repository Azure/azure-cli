# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.nic._create import Create as _NICCreate


class NICCreate(_NICCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            options=["--vnet-name"],
            arg_group="IP Configuration",
            help="Name of the virtual network.",
        )
        args_schema.subnet = AAZResourceIdArg(
            options=["--subnet"],
            arg_group="IP Configuration",
            help="Name or ID of an existing subnet. If name specified, please also specify `--vnet-name`; "
                 "If you want to use an existing subnet in other resource group, "
                 "please provide the ID instead of the name of the subnet.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/virtualNetworks/{vnet_name}/subnets/{}",
            ),
        )
        args_schema.application_security_groups = AAZListArg(
            options=["--application-security-groups", "--asgs"],
            arg_group="IP Configuration",
            help="Space-separated list of application security groups.",
        )
        args_schema.application_security_groups.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
        )
        args_schema.private_ip_address = AAZStrArg(
            options=["--private-ip-address"],
            arg_group="IP Configuration",
            help="Static private IP address to use.",
        )
        args_schema.private_ip_address_version = AAZStrArg(
            options=["--private-ip-address-version"],
            arg_group="IP Configuration",
            help="Version of private IP address to use.",
            enum=["IPv4", "IPv6"],
            default="IPv4",
        )
        args_schema.public_ip_address = AAZResourceIdArg(
            options=["--public-ip-address"],
            arg_group="IP Configuration",
            help="Name or ID of an existing public IP address.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/"
                         "publicIPAddresses/{}"
            ),
        )
        args_schema.gateway_name = AAZStrArg(
            options=["--gateway-name"],
            arg_group="Application Gateway",
            help="Name of the application gateway."
        )
        args_schema.app_gateway_address_pools = AAZListArg(
            options=["--app-gateway-address-pools", "--ag-address-pools"],
            arg_group="Application Gateway",
            help="Space-separated list of names or IDs of application gateway backend address pools to "
                 "associate with the NIC. If names are used, `--gateway-name` must be specified.",
        )
        args_schema.app_gateway_address_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/backendAddressPools/{}",
            ),
        )
        args_schema.lb_name = AAZStrArg(
            options=["--lb-name"],
            arg_group="Load Balancer",
            help="Name of the load balancer",
        )
        args_schema.lb_address_pools = AAZListArg(
            options=["--lb-address-pools"],
            arg_group="Load Balancer",
            help="Space-separated list of names or IDs of load balancer address pools to associate with the NIC. "
                 "If names are used, `--lb-name` must be specified.",
        )
        args_schema.lb_address_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/loadBalancers/{lb_name}/backendAddressPools/{}",
            ),
        )
        args_schema.lb_inbound_nat_rules = AAZListArg(
            options=["--lb-inbound-nat-rules"],
            arg_group="Load Balancer",
            help="Space-separated list of names or IDs of load balancer inbound NAT rules to associate with the NIC. "
                 "If names are used, `--lb-name` must be specified.",
        )
        args_schema.lb_inbound_nat_rules.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/loadBalancers/{lb_name}/inboundNatRules/{}",
            ),
        )
        args_schema.edge_zone = AAZStrArg(
            options=["--edge-zone"],
            help="Name of edge zone."
        )
        args_schema.network_security_group = AAZResourceIdArg(
            options=["--network-security-group"],
            help="Name or ID of an existing network security group",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/networkSecurityGroups/{}",
            ),
        )
        args_schema.extended_location._registered = False
        args_schema.ip_configurations._registered = False
        args_schema.nsg._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.network_security_group):
            args.nsg.id = args.network_security_group
        if has_value(args.edge_zone):
            args.extended_location.name = args.edge_zone
            args.extended_location.type = "EdgeZone"
        ip_configuration = {
            "name": "ipconfig1",
            "private_ip_address": args.private_ip_address,
            "private_ip_address_version": args.private_ip_address_version,  # when address doesn't exist, version should be ipv4 (default)
            "private_ip_allocation_method": "Static" if has_value(args.private_ip_address) else "Dynamic",
            "subnet": {"id": args.subnet} if has_value(args.subnet) else None,
            "public_ip_address": {"id": args.public_ip_address} if has_value(args.public_ip_address) else None,
            "application_security_groups": [{"id": x} for x in args.application_security_groups] if has_value(args.application_security_groups) else None,
            "application_gateway_backend_address_pools": [{"id": x} for x in args.app_gateway_address_pools] if has_value(args.app_gateway_address_pools) else None,
            "load_balancer_backend_address_pools": [{"id": x} for x in args.lb_address_pools] if has_value(args.lb_address_pools) else None,
            "load_balancer_inbound_nat_rules": [{"id": x} for x in args.lb_inbound_nat_rules] if has_value(args.lb_inbound_nat_rules) else None,
        }
        args.ip_configurations = [ip_configuration]

    def _output(self, *args, **kwargs):
        result = super()._output(*args, **kwargs)
        return {"NewNIC": result}
