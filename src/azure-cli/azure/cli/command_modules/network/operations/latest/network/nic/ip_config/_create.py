# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.command_modules.network.aaz.latest.network.nic.ip_config._create import Create as _NICIPConfigCreate


class NICIPConfigCreate(_NICIPConfigCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            options=["--vnet-name"],
            arg_group="IP Configuration",
            help="Name of the virtual network.",
        )
        args_schema.subnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/virtualNetworks/{vnet_name}/subnets/{}",
        )
        args_schema.public_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/"
                     "publicIPAddresses/{}"
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
        args_schema.application_gateway_backend_address_pools._registered = False
        args_schema.load_balancer_backend_address_pools._registered = False
        args_schema.load_balancer_inbound_nat_rules._registered = False
        args_schema.private_ip_allocation_method._registered = False
        args_schema.asgs_obj._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.private_ip_allocation_method = "Static" if has_value(args.private_ip_address) else "Dynamic"
        if has_value(args.private_ip_address_prefix_length) and has_value(args.make_primary) and \
                args.make_primary.to_serialized_data() is True:
            raise ArgumentUsageError(
                'usage error: When `--private-ip-address-prefix-length` is specified, `--make-primary` must be false')

        args.asgs_obj = assign_aaz_list_arg(
            args.asgs_obj,
            args.application_security_groups,
            element_transformer=lambda _, asg_id: {"id": asg_id}
        )
        args.application_gateway_backend_address_pools = assign_aaz_list_arg(
            args.application_gateway_backend_address_pools,
            args.app_gateway_address_pools,
            element_transformer=lambda _, pool_id: {"id": pool_id}
        )
        args.load_balancer_backend_address_pools = assign_aaz_list_arg(
            args.load_balancer_backend_address_pools,
            args.lb_address_pools,
            element_transformer=lambda _, pool_id: {"id": pool_id}
        )
        args.load_balancer_inbound_nat_rules = assign_aaz_list_arg(
            args.load_balancer_inbound_nat_rules,
            args.lb_inbound_nat_rules,
            element_transformer=lambda _, rule_id: {"id": rule_id}
        )

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if args.private_ip_address_version.to_serialized_data().lower() == "ipv4" and not has_value(args.subnet):
            primary = next(x for x in instance.properties.ip_configurations if x.properties.primary)
            args.subnet = primary.properties.subnet.id
        if args.make_primary.to_serialized_data():
            for config in instance.properties.ip_configurations:
                config.properties.primary = False
