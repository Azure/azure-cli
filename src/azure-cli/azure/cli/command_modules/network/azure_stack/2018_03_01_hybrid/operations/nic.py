# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from azure.cli.core.aaz import AAZResourceIdArgFormat, has_value, AAZListArg, AAZResourceIdArg, \
    AAZStrArg, AAZListArgFormat
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from knack.log import get_logger

from ._util import import_aaz_by_profile

logger = get_logger(__name__)


_NIC = import_aaz_by_profile("network.nic")


class NICCreate(_NIC.Create):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
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
        args_schema.network_security_group = AAZResourceIdArg(
            options=["--network-security-group"],
            help="Name or ID of an existing network security group",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/networkSecurityGroups/{}",
            ),
        )
        args_schema.ip_configurations._registered = False
        args_schema.nsg._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.network_security_group):
            args.nsg.id = args.network_security_group
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


class NICUpdate(_NIC.Update):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        class EmptyListArgFormat(AAZListArgFormat):
            def __call__(self, ctx, value):
                if value.to_serialized_data() == [""]:
                    logger.warning("It's recommended to detach it by null, empty string (\"\") will be deprecated.")
                    value._data = None
                return super().__call__(ctx, value)

        class EmptyResourceIdArgFormat(AAZResourceIdArgFormat):
            def __call__(self, ctx, value):
                if value._data == "":
                    logger.warning("It's recommended to detach it by null, empty string (\"\") will be deprecated.")
                    value._data = None
                return super().__call__(ctx, value)

        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_security_group = AAZResourceIdArg(
            options=["--network-security-group"],
            help="Name or ID of an existing network security group",
            fmt=EmptyResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/networkSecurityGroups/{}",
            ),
            nullable=True,
        )
        args_schema.dns_servers._fmt = EmptyListArgFormat()
        args_schema.nsg._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.network_security_group):
            args.nsg.id = args.network_security_group
        if has_value(args.internal_dns_name) and args.internal_dns_name == "":
            args.internal_dns_name = None

    def post_instance_update(self, instance):
        if not has_value(instance.properties.network_security_group.id):
            instance.properties.network_security_group = None


_NICIPConfig = import_aaz_by_profile("network.nic.ip_config")


class NICIPConfigCreate(_NICIPConfig.Create):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
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


class NICIPConfigUpdate(_NICIPConfig.Update):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):

        class EmptyListArgFormat(AAZListArgFormat):
            def __call__(self, ctx, value):
                if value.to_serialized_data() == [""]:
                    logger.warning("It's recommended to detach it by null, empty string (\"\") will be deprecated.")
                    value._data = None
                return super().__call__(ctx, value)

        class EmptyResourceIdArgFormat(AAZResourceIdArgFormat):
            def __call__(self, ctx, value):
                if value._data == "":
                    logger.warning("It's recommended to detach it by null, empty string (\"\") will be deprecated.")
                    value._data = None
                return super().__call__(ctx, value)

        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            options=["--vnet-name"],
            arg_group="IP Configuration",
            help="Name of the virtual network.",
            nullable=True,
        )
        args_schema.subnet._fmt = EmptyResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/virtualNetworks/{vnet_name}/subnets/{}",
        )
        args_schema.public_ip_address._fmt = EmptyResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/"
                     "publicIPAddresses/{}"
        )
        args_schema.application_security_groups = AAZListArg(
            options=["--application-security-groups", "--asgs"],
            arg_group="IP Configuration",
            help="Space-separated list of application security groups.",
            fmt=EmptyListArgFormat(),
            nullable=True,
        )
        args_schema.application_security_groups.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
            nullable=True,
        )
        args_schema.gateway_name = AAZStrArg(
            options=["--gateway-name"],
            arg_group="Application Gateway",
            help="Name of the application gateway.",
            nullable=True,
        )
        args_schema.app_gateway_address_pools = AAZListArg(
            options=["--app-gateway-address-pools", "--ag-address-pools"],
            arg_group="Application Gateway",
            help="Space-separated list of names or IDs of application gateway backend address pools to "
                 "associate with the NIC. If names are used, `--gateway-name` must be specified.",
            fmt=EmptyListArgFormat(),
            nullable=True,
        )
        args_schema.app_gateway_address_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/backendAddressPools/{}",
            ),
            nullable=True,
        )
        args_schema.lb_name = AAZStrArg(
            options=["--lb-name"],
            arg_group="Load Balancer",
            help="Name of the load balancer",
            nullable=True,
        )
        args_schema.lb_address_pools = AAZListArg(
            options=["--lb-address-pools"],
            arg_group="Load Balancer",
            help="Space-separated list of names or IDs of load balancer address pools to associate with the NIC. "
                 "If names are used, `--lb-name` must be specified.",
            fmt=EmptyListArgFormat(),
            nullable=True,
        )
        args_schema.lb_address_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/loadBalancers/{lb_name}/backendAddressPools/{}",
            ),
            nullable=True,
        )
        args_schema.lb_inbound_nat_rules = AAZListArg(
            options=["--lb-inbound-nat-rules"],
            arg_group="Load Balancer",
            help="Space-separated list of names or IDs of load balancer inbound NAT rules to associate with the NIC. "
                 "If names are used, `--lb-name` must be specified.",
            fmt=EmptyListArgFormat(),
            nullable=True,
        )
        args_schema.lb_inbound_nat_rules.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/loadBalancers/{lb_name}/inboundNatRules/{}",
            ),
            nullable=True,
        )
        args_schema.application_gateway_backend_address_pools._registered = False
        args_schema.load_balancer_backend_address_pools._registered = False
        args_schema.load_balancer_inbound_nat_rules._registered = False
        args_schema.private_ip_allocation_method._registered = False
        args_schema.asgs_obj._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.private_ip_address):
            if args.private_ip_address is None or args.private_ip_address == "":
                # switch private IP address allocation to dynamic if empty string is used
                args.private_ip_address = None
                args.private_ip_allocation_method = "Dynamic"
                args.private_ip_address_version = "IPv4"
            else:
                # if specific address provided, allocation is static
                args.private_ip_allocation_method = "Static"

    def pre_instance_update(self, instance):
        args = self.ctx.args
        instance = self.ctx.vars.instance
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
        # all ip configurations must belong to the same asgs
        is_primary = args.make_primary.to_serialized_data()
        for config in instance.properties.ip_configurations:
            if is_primary:
                config.properties.primary = False
            config.properties.application_security_groups = args.asgs_obj

    def post_instance_update(self, instance):
        if not has_value(instance.properties.subnet.id):
            instance.properties.subnet = None
        if not has_value(instance.properties.public_ip_address.id):
            instance.properties.public_ip_address = None


_LBPool = import_aaz_by_profile("network.nic.ip_config.lb_pool")

_AGPool = import_aaz_by_profile("network.nic.ip_config.ag_pool")


def add_nic_ip_config_address_pool(cmd, resource_group_name, network_interface_name, ip_config_name,
                                   backend_address_pool, load_balancer_name=None, application_gateway_name=None):

    class LBPoolAdd(_LBPool.Add):
        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
            return result["ipConfigurations"][0]

    class AGPoolAdd(_AGPool.Add):
        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
            return result["ipConfigurations"][0]

    arguments = {
        "ip_config_name": ip_config_name,
        "nic_name": network_interface_name,
        "resource_group": resource_group_name,
        "pool_id": backend_address_pool
    }
    if load_balancer_name:
        return LBPoolAdd(cli_ctx=cmd.cli_ctx)(command_args=arguments)
    if application_gateway_name:
        return AGPoolAdd(cli_ctx=cmd.cli_ctx)(command_args=arguments)


def remove_nic_ip_config_address_pool(cmd, resource_group_name, network_interface_name, ip_config_name,
                                      backend_address_pool, load_balancer_name=None, application_gateway_name=None):

    class LBPoolRemove(_LBPool.Remove):
        def _handler(self, command_args):
            lro_poller = super()._handler(command_args)
            lro_poller._result_callback = self._output
            return lro_poller

        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
            return result["ipConfigurations"][0]

    class AGPoolRemove(_AGPool.Remove):
        def _handler(self, command_args):
            lro_poller = super()._handler(command_args)
            lro_poller._result_callback = self._output
            return lro_poller

        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
            return result["ipConfigurations"][0]

    arguments = {
        "ip_config_name": ip_config_name,
        "nic_name": network_interface_name,
        "resource_group": resource_group_name,
        "pool_id": backend_address_pool
    }
    if load_balancer_name:
        return LBPoolRemove(cli_ctx=cmd.cli_ctx)(command_args=arguments)
    if application_gateway_name:
        return AGPoolRemove(cli_ctx=cmd.cli_ctx)(command_args=arguments)


_NICIPConfigNAT = import_aaz_by_profile("network.nic.ip_config.inbound_nat_rule")


class NICIPConfigNATAdd(_NICIPConfigNAT.Add):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lb_name = AAZStrArg(
            options=["--lb-name"],
            help="Name of the load balancer",
        )
        args_schema.inbound_nat_rule._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/loadBalancers/{lb_name}/inboundNatRules/{}",
        )
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result["ipConfigurations"][0]


class NICIPConfigNATRemove(_NICIPConfigNAT.Remove):

    def _handler(self, command_args):
        lro_poller = super()._handler(command_args)
        lro_poller._result_callback = self._output
        return lro_poller

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lb_name = AAZStrArg(
            options=["--lb-name"],
            help="Name of the load balancer",
        )
        args_schema.inbound_nat_rule._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/loadBalancers/{lb_name}/inboundNatRules/{}",
        )
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result["ipConfigurations"][0]
