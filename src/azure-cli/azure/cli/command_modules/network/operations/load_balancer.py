# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import register_command, AAZResourceIdArgFormat, has_value
from ..aaz.latest.network.lb import Delete as _LBDelete, Update as _LBUpdate, List as _LBList, Show as _LBShow
from ..aaz.latest.network.lb.frontend_ip import Create as _LBFrontendIPCreate, Update as _LBFrontendIPUpdate, \
    Show as _LBFrontendIPShow, Delete as _LBFrontendIPDelete, List as _LBFrontendIPList
from ..aaz.latest.network.lb.inbound_nat_pool import Create as _LBInboundNatPoolCreate, \
    Update as _LBInboundNatPoolUpdate
from ..aaz.latest.network.lb.inbound_nat_rule import Create as _LBInboundNatRuleCreate, \
    Update as _LBInboundNatRuleUpdate
from ..aaz.latest.network.lb.rule import Create as _LBRuleCreate, Update as _LBRuleUpdate, Show as _LBRuleShow, \
    Delete as _LBRuleDelete, List as _LBRuleList
from ..aaz.latest.network.lb.outbound_rule import Create as _LBOutboundRuleCreate, Update as _LBOutboundRuleUpdate
# from ..aaz.latest.network.lb.address_pool import Create as _LBAddressPoolCreate, Update as _LBAddressPoolUpdate, \
#     Show as _LBAddressPoolShow, List as _LBAddressPoolList, Delete as _LBAddressPoolDelete

from ..aaz.latest.network.cross_region_lb.address_pool import Create as _CrossRegionLoadBalancerAddressPoolCreate, \
    Update as _CrossRegionLoadBalancerAddressPoolUpdate
from ..aaz.latest.network.cross_region_lb.address_pool.address import Add as _CrossRegionLoadBalancerAddressPoolAddressAdd, \
    Update as _CrossRegionLoadBalancerAddressPoolAddressUpdate, Remove as _CrossRegionLoadBalancerAddressPoolAddressRemove


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
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
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


class LBInboundNatPoolUpdate(_LBInboundNatPoolUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_name._fmt = EmptyResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        return args_schema

    def post_instance_update(self, instance):
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None


class LBInboundNatRuleCreate(_LBInboundNatRuleCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.backend_address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
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


class LBInboundNatRuleUpdate(_LBInboundNatRuleUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.backend_address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
        )
        return args_schema

    def post_instance_update(self, instance):
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None
        if not has_value(instance.properties.backend_address_pool.id):
            instance.properties.backend_address_pool = None


class LBRuleCreate(_LBRuleCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.probe_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{}"
        )
        # list argument accept one element: `--backend-pool-name PoolName`
        args_schema.backend_pools = AAZListArg(
            options=["--backend-pools-name", "--backend-pool-name"],
            arg_group="Properties",
            help="List of ID or name of the backend address pools. Multiple pools are only supported by Gateway SKU load balancer. If only one exists, omit to use as default."
        )
        args_schema.backend_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
            )
        )

        args_schema.protocol._required = True
        args_schema.frontend_port._required = True
        args_schema.backend_port._required = True
        args_schema.backend_address_pools._registered = False
        return args_schema

    def pre_instance_create(self):
        from azure.cli.core.aaz.utils import assign_aaz_list_arg
        args = self.ctx.args
        if not has_value(args.frontend_ip_name):
            instance = self.ctx.vars.instance
            frontend_ip_configurations = instance.properties.frontend_ip_configurations
            if len(frontend_ip_configurations) == 1:
                args.frontend_ip_name = instance.properties.frontend_ip_configurations[0].id
            elif len(frontend_ip_configurations) > 1:
                raise ArgumentUsageError(
                    "Multiple FrontendIpConfigurations found in loadbalancer. Specify --frontend-ip explicitly.")
        if not has_value(args.backend_pools):
            instance = self.ctx.vars.instance
            backend_address_pools = instance.properties.backend_address_pools
            if len(backend_address_pools) == 1:
                args.backend_pools = [instance.properties.backend_address_pools[0].id]
            elif len(backend_address_pools) > 1:
                raise ArgumentUsageError(
                    "Multiple BackendAddressPools found in loadbalancer. Specify --backend-pool-name explicitly.")
        args.backend_address_pools = assign_aaz_list_arg(
            args.backend_address_pools, args.backend_pools,
            element_transformer=lambda _, id: {"id": id}
        )


class LBRuleUpdate(_LBRuleUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.probe_name._fmt = EmptyResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{}"
        )

        args_schema.backend_pools = AAZListArg(
            options=["--backend-pools-name", "--backend-pool-name"],
            nullable=True,
            arg_group="Properties",
            help="List of ID or name of the backend address pools. Multiple pools are only supported by Gateway SKU load balancer."
        )

        args_schema.backend_pools.Element = AAZResourceIdArg(
            nullable=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
            )
        )

        args_schema.protocol._nullable = False
        args_schema.frontend_port._nullable = False
        args_schema.backend_port._nullable = False
        args_schema.backend_address_pools._registered = False
        return args_schema

    def pre_operations(self):
        from azure.cli.core.aaz.utils import assign_aaz_list_arg
        args = self.ctx.args
        args.backend_address_pools = assign_aaz_list_arg(
            args.backend_address_pools, args.backend_pools,
            element_transformer=lambda _, id: {"id": id}
        )

    def post_instance_update(self, instance):
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None
        if not has_value(instance.properties.probe.id):
            instance.properties.probe = None
        # always remove backend_address_pool in update request, service will fill this property based on backend_address_pools property.
        instance.properties.backend_address_pool = None


class LBOutboundRuleCreate(_LBOutboundRuleCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.backend_address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
        )
        args_schema.frontend_ip_configs = AAZListArg(
            options=["--frontend-ip-configs"],
            arg_group="Properties",
            help="The List of frontend IP configuration IDs or names.",
        )
        args_schema.frontend_ip_configs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
            )
        )

        args_schema.protocol._required = True
        args_schema.backend_address_pool._required = True
        args_schema.frontend_ip_configurations._registered = False
        return args_schema

    def pre_operations(self):
        from azure.cli.core.aaz.utils import assign_aaz_list_arg
        args = self.ctx.args
        args.frontend_ip_configurations = assign_aaz_list_arg(
            args.frontend_ip_configurations,
            args.frontend_ip_configs,
            element_transformer=lambda _, id: {"id": id}
        )


class LBOutboundRuleUpdate(_LBOutboundRuleUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.backend_address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
        )
        args_schema.frontend_ip_configs = AAZListArg(
            options=["--frontend-ip-configs"],
            arg_group="Properties",
            help="The List of frontend IP configuration IDs or names.",
        )
        args_schema.frontend_ip_configs.Element = AAZResourceIdArg(
            nullable=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
            )
        )

        args_schema.protocol._nullable = False
        args_schema.backend_address_pool._nullable = False
        args_schema.frontend_ip_configurations._registered = False
        return args_schema

    def pre_operations(self):
        from azure.cli.core.aaz.utils import assign_aaz_list_arg
        args = self.ctx.args
        args.frontend_ip_configurations = assign_aaz_list_arg(
            args.frontend_ip_configurations,
            args.frontend_ip_configs,
            element_transformer=lambda _, id: {"id": id}
        )


# cross-region-lb commands
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


@register_command("network cross-region-lb rule show")
class CrossRegionLoadBalancerRuleShow(_LBRuleShow):
    """Get the details of a load balancing rule.

    :example: Get the details of a load balancing rule.
        az network cross-region-lb rule show -g MyResourceGroup --lb-name MyLb -n MyLbRule
    """


@register_command("network cross-region-lb rule delete")
class CrossRegionLoadBalancerRuleDelete(_LBRuleDelete):
    """Delete a load balancing rule.

    :example: Delete a load balancing rule.
        az network cross-region-lb rule delete -g MyResourceGroup --lb-name MyLb -n MyLbRule
    """


@register_command("network cross-region-lb rule list")
class CrossRegionLoadBalancerRuleList(_LBRuleList):
    """List load balancing rules.

    :example: List load balancing rules.
        az network cross-region-lb rule list -g MyResourceGroup --lb-name MyLb -o table
    """


@register_command("network cross-region-lb rule create")
class CrossRegionLoadBalancerRuleCreate(_LBRuleCreate):
    """Create a load balancing rule.

    :example: Create a load balancing rule that assigns a front-facing IP configuration and port to an address pool and port.
        az network cross-region-lb rule create -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Tcp --frontend-ip-name MyFrontEndIp --frontend-port 80 --backend-pool-name MyAddressPool --backend-port 80

    :example: Create a load balancing rule that assigns a front-facing IP configuration and port to an address pool and port with the floating ip feature.
        az network cross-region-lb rule create -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Tcp --frontend-ip-name MyFrontEndIp --frontend-port 80 --backend-pool-name MyAddressPool --backend-port 80 --floating-ip true

    :example: Create an HA ports load balancing rule that assigns a frontend IP and port to use all available backend IPs in a pool on the same port.
        az network cross-region-lb rule create -g MyResourceGroup --lb-name MyLb -n MyHAPortsRule --protocol All --frontend-port 0 --backend-port 0 --frontend-ip-name MyFrontendIp --backend-pool-name MyAddressPool
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.probe_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{}"
        )
        # not support multi backend pools because the loadbalance SKU is not Gateway
        args_schema.backend_pool = AAZResourceIdArg(
            options=["--backend-pool-name"],
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
            ),
            arg_group="Properties",
            help="ID or name of the backend address pools. If only one exists, omit to use as default."
        )

        args_schema.protocol._required = True
        args_schema.frontend_port._required = True
        args_schema.backend_port._required = True
        args_schema.backend_address_pools._registered = False
        args_schema.disable_outbound_snat._registered = False   # it's not required for cross-region-lb
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
        if not has_value(args.backend_pool):
            instance = self.ctx.vars.instance
            backend_address_pools = instance.properties.backend_address_pools
            if len(backend_address_pools) == 1:
                args.backend_pool = instance.properties.backend_address_pools[0].id
            elif len(backend_address_pools) > 1:
                raise ArgumentUsageError(
                    "Multiple BackendAddressPools found in loadbalancer. Specify --backend-pool-name explicitly.")
        if has_value(args.backend_pool):
            args.backend_address_pools = [{"id": args.backend_pool.to_serialized_data()}]


@register_command("network cross-region-lb rule update")
class CrossRegionLoadBalancerRuleUpdate(_LBRuleUpdate):
    """Update a load balancing rule.

    :example:  Update a load balancing rule to change the protocol to UDP.
        az network cross-region-lb rule update -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol Udp

    :example: Update a load balancing rule to support HA ports.
        az network cross-region-lb rule update -g MyResourceGroup --lb-name MyLb -n MyLbRule --protocol All --frontend-port 0 --backend-port 0
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.probe_name._fmt = EmptyResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{}"
        )
        # not support multi backend pools because the loadbalance SKU is not Gateway
        args_schema.backend_pool = AAZResourceIdArg(
            options=["--backend-pool-name"],
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{}"
            ),
            arg_group="Properties",
            nullable=True,
            help="ID or name of the backend address pools. If only one exists, omit to use as default."
        )

        args_schema.protocol._nullable = False
        args_schema.frontend_port._nullable = False
        args_schema.backend_port._nullable = False
        args_schema.backend_address_pools._registered = False
        args_schema.disable_outbound_snat._registered = False   # it's not required for cross-region-lb
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.backend_pool):
            backend_pool = args.backend_pool.to_serialized_data()
            if backend_pool is None:
                args.backend_address_pools = []  # remove backend pool
            else:
                args.backend_address_pools = [{"id": backend_pool}]

    def post_instance_update(self, instance):
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None
        if not has_value(instance.properties.probe.id):
            instance.properties.probe = None
        # always remove backend_address_pool in update request, service will fill this property based on backend_address_pools property.
        instance.properties.backend_address_pool = None


class CrossRegionLoadBalancerAddressPoolCreate(_CrossRegionLoadBalancerAddressPoolCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        # not support name, the frontend id should belong to a regional load balance
        args_schema.backend_addresses.Element.frontend_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}"
        )
        args_schema.backend_addresses.Element.name._required = True
        args_schema.backend_addresses.Element.frontend_ip_address._required = True
        return args_schema


class CrossRegionLoadBalancerAddressPoolUpdate(_CrossRegionLoadBalancerAddressPoolUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        # not support name, the frontend id should belong to a regional load balance
        args_schema.backend_addresses.Element.frontend_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}"
        )
        args_schema.backend_addresses.Element.name._nullable = False
        args_schema.backend_addresses.Element.frontend_ip_address._nullable = False
        return args_schema


class CrossRegionLoadBalancerAddressPoolAddressAdd(_CrossRegionLoadBalancerAddressPoolAddressAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}"
        )

        args_schema.frontend_ip_address._required = True
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class CrossRegionLoadBalancerAddressPoolAddressRemove(_CrossRegionLoadBalancerAddressPoolAddressRemove):

    def _handler(self, command_args):
        lro_poller = super()._handler(command_args)
        lro_poller._result_callback = self._output
        return lro_poller

    def _output(self, *args, **kwargs):  # pylint: disable=unused-argument
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class CrossRegionLoadBalancerAddressPoolAddressUpdate(_CrossRegionLoadBalancerAddressPoolAddressUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}"
        )

        args_schema.frontend_ip_address._nullable = False
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
