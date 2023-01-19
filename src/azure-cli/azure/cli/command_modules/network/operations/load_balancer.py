# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger
from azure.cli.core.azclierror import ArgumentUsageError, InvalidArgumentValueError
from azure.cli.core.aaz import register_command, AAZResourceIdArgFormat, has_value
from ..aaz.latest.network.lb import Delete as _LBDelete, Update as _LBUpdate, List as _LBList, Show as _LBShow
from ..aaz.latest.network.lb.frontend_ip import Create as _LBFrontendIPCreate, Update as _LBFrontendIPUpdate, \
    Show as _LBFrontendIPShow, Delete as _LBFrontendIPDelete, List as _LBFrontendIPList
from ..aaz.latest.network.lb.inbound_nat_pool import Create as _LBInboundNatPoolCreate, \
    Update as _LBInboundNatPoolUpdate, Show as _LBInboundNatPoolShow, Delete as _LBInboundNatPoolDelete, \
    List as _LBInboundNatPoolList


logger = get_logger(__name__)


class EmptyResourceIdArgFormat(AAZResourceIdArgFormat):
    def __call__(self, ctx, value):
        if value._data == "":
            logger.warning("It's recommended to detach it by null, empty string (\"\") will be deprecated.")
            value._data = None
        return super().__call__(ctx, value)


class LBFrontendIPCreate(_LBFrontendIPCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZArgEnum
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


class LBFrontendIPUpdate(_LBFrontendIPUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            arg_group="Properties",
            options=['--vnet-name'],
            help="The virtual network (VNet) associated with the subnet (Omit if supplying a subnet id)."
        )
        args_schema.subnet._fmt = EmptyResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{}",
        )
        args_schema.public_ip_prefix._fmt = EmptyResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIpPrefixes/{}",
        )
        args_schema.public_ip_address._fmt = EmptyResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{}",
        )
        args_schema.gateway_lb._fmt = EmptyResourceIdArgFormat(
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


class LBInboundNatPoolCreate(_LBInboundNatPoolCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_name = AAZStrArg(
            options=["--frontend-ip-name"],
            arg_group="Properties",
            help="The name the frontend IP configuration. If only one exists, omit to use as default.",
        )

        args_schema.frontend_ip._registered = False
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if has_value(args.frontend_ip_name):
            frontend_ip_name = args.frontend_ip_name.to_serialized_data()
            for frontend_ip in instance.properties.frontend_ip_configurations:
                if frontend_ip.name == frontend_ip_name:
                    args.frontend_ip = frontend_ip.id
                    break
            if not has_value(args.frontend_ip):
                raise InvalidArgumentValueError(
                    "FrontendIpConfiguration '{}' does not exist".format(frontend_ip_name))
        elif has_value(instance.properties.frontend_ip_configurations) and len(instance.properties.frontend_ip_configurations) == 1:
            args.frontend_ip = instance.properties.frontend_ip_configurations[0].id


class LBInboundNatPoolUpdate(_LBInboundNatPoolUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_name = AAZStrArg(
            options=["--frontend-ip-name"],
            arg_group="Properties",
            help="The name the frontend IP configuration.",
            nullable=True
        )

        args_schema.frontend_ip._registered = False
        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if has_value(args.frontend_ip_name):
            frontend_ip_name = args.frontend_ip_name.to_serialized_data()
            if frontend_ip_name is None:
                args.frontend_ip = None
            else:
                for frontend_ip in instance.properties.frontend_ip_configurations:
                    if frontend_ip.name == frontend_ip_name:
                        args.frontend_ip = frontend_ip.id
                        break
                if not has_value(args.frontend_ip):
                    raise InvalidArgumentValueError(
                        "FrontendIpConfiguration '{}' does not exist".format(frontend_ip_name))

    def post_instance_update(self, instance):
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None


@register_command("network cross-region-lb show")
class CrossRegionLoadBalancerShow(_LBShow):
    """Get the details of a load balancer.

    :example: Get the details of a load balancer.
        az network cross-region-lb show -g MyResourceGroup -n MyLb
    """


@register_command("network cross-region-lb delete")
class CrossRegionLoadBalancerDelete(_LBDelete):
    """Delete the specified load balancer.

    :example: Delete a load balancer.
        az network cross-region-lb delete -g MyResourceGroup -n MyLb
    """


@register_command("network cross-region-lb list")
class CrossRegionLoadBalancerList(_LBList):
    """List load balancers.

    :example: List load balancers.
        az network cross-region-lb list -g MyResourceGroup
    """


@register_command("network cross-region-lb update")
class CrossRegionLoadBalancerUpdate(_LBUpdate):
    """Update a load balancer.

    This command can only be used to update the tags for a load balancer.
    Name and resource group are immutable and cannot be updated.

    :example: Update the tags of a load balancer.
        az network cross-region-lb update -g MyResourceGroup -n MyLB --tags CostCenter=MyTestGroup
    """


@register_command("network cross-region-lb frontend-ip show")
class CrossRegionLoadBalancerFrontendIPShow(_LBFrontendIPShow):
    """Get the details of a frontend IP address.

    :example: Get the details of a frontend IP address.
        az network cross-region-lb frontend-ip show -g MyResourceGroup --lb-name MyLb -n MyFrontendIp
    """


@register_command("network cross-region-lb frontend-ip list")
class CrossRegionLoadBalancerFrontendIPList(_LBFrontendIPList):
    """List frontend IP addresses.

    :example: List frontend IP addresses.
        az network cross-region-lb frontend-ip list -g MyResourceGroup --lb-name MyLb
    """


@register_command("network cross-region-lb frontend-ip delete")
class CrossRegionLoadBalancerFrontendIPDelete(_LBFrontendIPDelete):
    """Delete a frontend IP address.

    :example: Delete a frontend IP address.
        az network cross-region-lb frontend-ip delete -g MyResourceGroup --lb-name MyLb -n MyFrontendIp
    """


@register_command("network cross-region-lb frontend-ip create")
class CrossRegionLoadBalancerFrontendIPCreate(_LBFrontendIPCreate):
    """Create a frontend IP address.

    :example: Create a frontend ip address for a public load balancer.
        az network cross-region-lb frontend-ip create -g MyResourceGroup --lb-name MyLb -n MyFrontendIp --public-ip-address MyFrontendIp
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZArgEnum

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


@register_command("network cross-region-lb frontend-ip update")
class CrossRegionLoadBalancerFrontendIPUpdate(_LBFrontendIPUpdate):
    """Update a frontend IP address.

    :example: Update the frontend IP address of a public load balancer.
        az network cross-region-lb frontend-ip update -g MyResourceGroup --lb-name MyLb -n MyFrontendIp --public-ip-address MyFrontendIp
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZArgEnum

        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_prefix._fmt = EmptyResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIpPrefixes/{}",
        )
        args_schema.public_ip_address._fmt = EmptyResourceIdArgFormat(
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
