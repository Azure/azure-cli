# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import AAZResourceIdArgFormat, has_value, AAZStrArg, AAZArgEnum
from ._util import import_aaz_by_profile


logger = get_logger(__name__)


_LBFrontendIP = import_aaz_by_profile("network.lb.frontend_ip")


class LBFrontendIPCreate(_LBFrontendIP.Create):

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
        args_schema.public_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{}",
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
        if has_value(args.subnet) and has_value(args.public_ip_address):
            raise ArgumentUsageError(
                'incorrect usage: --subnet NAME --vnet-name NAME | '
                '--subnet ID | --public-ip-address NAME_OR_ID')

        if not has_value(args.public_ip_address):
            logger.warning(
                "Please note that the default public IP used for LB frontend will be changed from Basic to Standard "
                "in the future."
            )

        if has_value(args.private_ip_address):
            args.private_ip_allocation_method = 'Static'
        else:
            args.private_ip_allocation_method = 'Dynamic'


class LBFrontendIPUpdate(_LBFrontendIP.Update):

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
        args_schema.public_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{}",
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


_LBInboundNatPool = import_aaz_by_profile("network.lb.inbound_nat_pool")


class LBInboundNatPoolCreate(_LBInboundNatPool.Create):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )

        args_schema.protocol._required = True
        args_schema.backend_port._required = True
        args_schema.frontend_port_range_start._required = True
        args_schema.frontend_port_range_end._required = True
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        if not has_value(args.frontend_ip_name):
            instance = self.ctx.vars.instance
            frontend_ip_configurations = instance.properties.frontend_ip_configurations
            if len(frontend_ip_configurations) == 1:
                args.frontend_ip_name = instance.properties.frontend_ip_configurations[0].id
            elif len(frontend_ip_configurations) > 1:
                raise ArgumentUsageError("Multiple FrontendIpConfigurations found in loadbalancer. Specify --frontend-ip explicitly.")


class LBInboundNatPoolUpdate(_LBInboundNatPool.Update):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )

        args_schema.protocol._nullable = False
        args_schema.backend_port._nullable = False
        args_schema.frontend_port_range_start._nullable = False
        args_schema.frontend_port_range_end._nullable = False
        return args_schema

    def post_instance_update(self, instance):
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None


_LBInboundNatRule = import_aaz_by_profile("network.lb.inbound_nat_rule")


class LBInboundNatRuleCreate(_LBInboundNatRule.Create):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )

        # required for a public load balancer
        args_schema.protocol._required = True
        args_schema.backend_port._required = True
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        if not has_value(args.frontend_ip_name):
            instance = self.ctx.vars.instance
            frontend_ip_configurations = instance.properties.frontend_ip_configurations
            if len(frontend_ip_configurations) == 1:
                args.frontend_ip_name = instance.properties.frontend_ip_configurations[0].id
            elif len(frontend_ip_configurations) > 1:
                raise ArgumentUsageError("Multiple FrontendIpConfigurations found in loadbalancer. Specify --frontend-ip explicitly.")


class LBInboundNatRuleUpdate(_LBInboundNatRule.Update):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        return args_schema

    def post_instance_update(self, instance):
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None


_LBRule = import_aaz_by_profile("network.lb.rule")


class LBRuleCreate(_LBRule.Create):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.probe_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{}"
        )
        args_schema.backend_address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
        )

        args_schema.protocol._required = True
        args_schema.frontend_port._required = True
        args_schema.backend_port._required = True

        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        if not has_value(args.frontend_ip_name):
            instance = self.ctx.vars.instance
            frontend_ip_configurations = instance.properties.frontend_ip_configurations
            if len(frontend_ip_configurations) == 1:
                args.frontend_ip_name = instance.properties.frontend_ip_configurations[0].id
            elif len(frontend_ip_configurations) > 1:
                raise ArgumentUsageError(
                    "Multiple FrontendIpConfigurations found in loadbalancer. Specify --frontend-ip explicitly.")
        if not has_value(args.backend_address_pool):
            instance = self.ctx.vars.instance
            backend_address_pools = instance.properties.backend_address_pools
            if len(backend_address_pools) == 1:
                args.backend_address_pool = instance.properties.backend_address_pools[0].id
            elif len(backend_address_pools) > 1:
                raise ArgumentUsageError(
                    "Multiple BackendAddressPools found in loadbalancer. Specify --backend-pool-name explicitly.")


class LBRuleUpdate(_LBRule.Update):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.probe_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{}"
        )

        args_schema.backend_address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
        )

        args_schema.protocol._nullable = False
        args_schema.frontend_port._nullable = False
        args_schema.backend_port._nullable = False
        return args_schema

    def post_instance_update(self, instance):
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None
        if not has_value(instance.properties.probe.id):
            instance.properties.probe = None
        if not has_value(instance.properties.backend_address_pool.id):
            instance.properties.backend_address_pool = None


_LBProbe = import_aaz_by_profile("network.lb.probe")


class LBProbeCreate(_LBProbe.Create):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.port._required = True
        args_schema.protocol._required = True
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.request_path) and args.request_path == "":
            args.request_path = None


class LBProbeUpdate(_LBProbe.Update):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.port._nullable = False
        args_schema.protocol._nullable = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.request_path) and args.request_path == "":
            args.request_path = None
