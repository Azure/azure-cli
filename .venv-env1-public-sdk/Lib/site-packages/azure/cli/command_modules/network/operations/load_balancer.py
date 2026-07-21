# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import register_command, AAZResourceIdArgFormat, has_value, AAZListArg, AAZResourceIdArg, \
    AAZStrArg, AAZArgEnum
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
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
from ..aaz.latest.network.lb.address_pool import Create as _LBAddressPoolCreate, Update as _LBAddressPoolUpdate, \
    Show as _LBAddressPoolShow, Delete as _LBAddressPoolDelete, List as _LBAddressPoolList
from ..aaz.latest.network.lb.address_pool.address import Add as _LBAddressPoolAddressAdd, \
    Update as _LBAddressPoolAddressUpdate, Show as _LBAddressPoolAddressShow, \
    Remove as _LBAddressPoolAddressRemove, List as _LBAddressPoolAddressList
from ..aaz.latest.network.lb.address_pool.basic import Create as _LBAddressPoolBasicCreate, \
    Delete as _LBAddressPoolBasicDelete
from ..aaz.latest.network.lb.address_pool.tunnel_interface import Add as _LBAddressPoolTunnelInterfaceAdd, \
    Update as _LBAddressPoolTunnelInterfaceUpdate
from ..aaz.latest.network.lb.probe import Create as _LBProbeCreate, Update as _LBProbeUpdate


logger = get_logger(__name__)


class LBFrontendIPCreate(_LBFrontendIPCreate):

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
        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
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

    def post_instance_create(self, instance):
        args = self.ctx.args
        if has_value(args.frontend_ip_name):
            curr_id = args.frontend_ip_name.to_serialized_data()
            curr_name = parse_resource_id(curr_id)["resource_name"] if is_valid_resource_id(curr_id) else curr_id

            parent = self.ctx.vars.instance
            frontend_ip_configurations = parent.properties.frontend_ip_configurations
            for fip in frontend_ip_configurations:
                if fip.name == curr_name:
                    if has_value(fip.properties.gateway_load_balancer):
                        rid = fip.properties.gateway_load_balancer.id.to_serialized_data()
                        self.ctx.update_aux_subscriptions(parse_resource_id(rid)["subscription"])


class LBRuleUpdate(_LBRuleUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{}"
        )
        args_schema.probe_name._fmt = AAZResourceIdArgFormat(
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

        args = self.ctx.args
        if has_value(args.frontend_ip_name):
            curr_id = args.frontend_ip_name.to_serialized_data()
            curr_name = parse_resource_id(curr_id)["resource_name"] if is_valid_resource_id(curr_id) else curr_id

            parent = self.ctx.vars.instance
            frontend_ip_configurations = parent.properties.frontend_ip_configurations
            for fip in frontend_ip_configurations:
                if fip.name == curr_name:
                    if has_value(fip.properties.gateway_load_balancer):
                        rid = fip.properties.gateway_load_balancer.id.to_serialized_data()
                        self.ctx.update_aux_subscriptions(parse_resource_id(rid)["subscription"])


class LBOutboundRuleCreate(_LBOutboundRuleCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
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


@register_command("network lb address-pool create")
class LBAddressPoolCreate(_LBAddressPoolBasicCreate):
    """Create load balancer backend address pool.

    :example: Create an address pool.
        az network lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool

    :example: Create an address pool with several backend addresses using shorthand syntax arguments.
        az network lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool --vnet MyVnetResource --backend-addresses "[{name:addr1,ip-address:10.0.0.1},{name:addr2,ip-address:10.0.0.2,subnet:subnetName}]"

    :example: Create an address pool with several backend addresses using config file
        az network lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool --backend-addresses config_file.json

    :example: Create an address pool with one backend address using key-value arguments.
        az network lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool --backend-address name=addr1 ip-address=10.0.0.1 subnet=/subscriptions/000/resourceGroups/MyRg/providers/Microsoft.Network/virtualNetworks/vnet/subnets/subnet1
    """

    # inherient the BackendAddressPoolsCreateOrUpdate operation
    class LoadBalancerBackendAddressPoolsCreateOrUpdate(_LBAddressPoolCreate.LoadBalancerBackendAddressPoolsCreateOrUpdate):

        def on_200_201(self, session):
            # ignore the response data.
            pass

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet = AAZResourceIdArg(
            options=["--vnet"],
            arg_group="Properties",
            help="Name or Id of the default virtual network applied to backend addresses in `--backend-addresses`.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
            )
        )

        args_schema.admin_state = AAZStrArg(
            options=["--admin-state"],
            arg_group="Properties",
            help="Default administrative state to backend addresses in `--backend-addresses`.",
        )
        args_schema.admin_state.enum = args_schema.backend_addresses.Element.admin_state.enum

        args_schema.backend_addresses.Element.virtual_network._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
        )

        args_schema.backend_addresses.Element.name._required = True
        args_schema.backend_addresses.Element.ip_address._required = True
        args_schema.backend_addresses.Element.frontend_ip_address._registered = False
        args_schema.vnet_id._registered = False
        return args_schema

    def _execute_operations(self):
        self.pre_operations()
        self.LoadBalancersGet(ctx=self.ctx)()
        self.pre_instance_create()
        sku = self.ctx.vars.instance.sku.name.to_serialized_data()
        if sku.lower() == "basic":
            self.InstanceCreateByJson(ctx=self.ctx)()
            self.post_instance_create(self.ctx.selectors.subresource.required())
            yield self.LoadBalancersCreateOrUpdate(ctx=self.ctx)()
        else:
            # use AddressPoolsCreateOrUpdate API to update Standarded or Geteway lb
            yield self.LoadBalancerBackendAddressPoolsCreateOrUpdate(ctx=self.ctx)()
            self.LoadBalancersGet(ctx=self.ctx)()
        self.post_operations()

    def pre_operations(self):
        from azure.cli.core.aaz import AAZUndefined

        args = self.ctx.args
        if has_value(args.sync_mode) and has_value(args.vnet):
            args.vnet_id = args.vnet
            args.vnet = AAZUndefined
        if has_value(args.backend_addresses):
            for backend_address in args.backend_addresses:
                if not has_value(backend_address.admin_state) and has_value(args.admin_state):
                    # use the command level argument --admin-state
                    backend_address.admin_state = args.admin_state

                virtual_network = backend_address.virtual_network.to_serialized_data()
                if not virtual_network and has_value(args.vnet):
                    # use the command level argument --vnet
                    virtual_network = args.vnet.to_serialized_data()
                    backend_address.virtual_network = virtual_network

                subnet = backend_address.subnet.to_serialized_data()
                if subnet and not is_valid_resource_id(subnet):
                    if not virtual_network:
                        raise ArgumentUsageError(
                            "Invalid backend address `{}`: vnet name or vnet ID is required when using subnet name only.".format(
                                backend_address.name)
                        )
                    # convert subnet name to subnet id
                    subnet = f"{virtual_network}/subnets/{subnet}"
                    backend_address.subnet = subnet

                if not virtual_network and not subnet:
                    raise ArgumentUsageError(
                        "Invalid backend address `{}`: vnet or subnet is required.".format(
                            backend_address.name)
                    )

    def pre_instance_create(self):
        args = self.ctx.args
        if not has_value(args.tunnel_interfaces):
            instance = self.ctx.vars.instance
            if has_value(instance.sku.name) and instance.sku.name.to_serialized_data().lower() == 'gateway':
                # when sku is 'gateway', 'tunnelInterfaces' can't be None. Otherwise, service will respond error
                args.tunnel_interfaces = [{"identifier": 900, "type": 'Internal', "protocol": 'VXLAN'}]


class LBAddressPoolUpdate(_LBAddressPoolUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet = AAZResourceIdArg(
            options=["--vnet"],
            arg_group="Properties",
            help="Name or Id of the default virtual network applied to backend addresses in `--backend-addresses`.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
            )
        )
        args_schema.admin_state = AAZStrArg(
            options=["--admin-state"],
            arg_group="Properties",
            help="Default administrative state to backend addresses in `--backend-addresses`.",
        )
        args_schema.admin_state.enum = args_schema.backend_addresses.Element.admin_state.enum

        args_schema.backend_addresses.Element.virtual_network._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
        )

        args_schema.backend_addresses.Element.name._nullable = False
        args_schema.backend_addresses.Element.ip_address._nullable = False
        args_schema.backend_addresses.Element.frontend_ip_address._registered = False
        args_schema.vnet_id._registered = False
        return args_schema

    def pre_operations(self):
        from azure.cli.core.aaz import AAZUndefined

        args = self.ctx.args
        if has_value(args.sync_mode) and has_value(args.vnet):
            args.vnet_id = args.vnet
            args.vnet = AAZUndefined
        if has_value(args.backend_addresses) and args.backend_addresses.to_serialized_data() is not None:
            for backend_address in args.backend_addresses:
                if not has_value(backend_address.admin_state) and has_value(args.admin_state):
                    # use the command level argument --admin-state
                    backend_address.admin_state = args.admin_state
                if not has_value(backend_address.virtual_network) and has_value(args.vnet):
                    # use the command level argument --vnet
                    backend_address.virtual_network = args.vnet
                subnet = backend_address.subnet.to_serialized_data()
                if subnet and not is_valid_resource_id(subnet):
                    virtual_network = backend_address.virtual_network.to_serialized_data()
                    if not virtual_network:
                        raise ArgumentUsageError(
                            "Invalid backend address: vnet name or vnet ID is required when using subnet name only."
                        )
                    # convert subnet name to subnet id
                    subnet = f"{virtual_network}/subnets/{subnet}"
                    backend_address.subnet = subnet

    def post_instance_update(self, instance):
        if has_value(instance.properties.load_balancer_backend_addresses):
            for backend_address in instance.properties.load_balancer_backend_addresses:
                if not has_value(backend_address.properties.virtual_network.id):
                    backend_address.properties.virtual_network = None
                if not has_value(backend_address.properties.subnet.id):
                    backend_address.properties.subnet = None


@register_command("network lb address-pool delete")
class LBAddressPoolDelete(_LBAddressPoolBasicDelete):
    """Delete the specified load balancer backend address pool.

    :example: Delete an address pool.
        az network lb address-pool delete -g MyResourceGroup --lb-name MyLb -n MyAddressPool
    """


class LBAddressPoolAddressAdd(_LBAddressPoolAddressAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.virtual_network._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
        )
        args_schema.ip_address._required = True
        args_schema.frontend_ip_address._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        virtual_network = args.virtual_network.to_serialized_data()
        subnet = args.subnet.to_serialized_data()
        if subnet and not is_valid_resource_id(subnet):
            if not virtual_network:
                raise ArgumentUsageError(
                    "vnet name or vnet ID is required when using subnet name only."
                )
            # convert subnet name to subnet id
            subnet = f"{virtual_network}/subnets/{subnet}"
            args.subnet = subnet

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class LBAddressPoolAddressUpdate(_LBAddressPoolAddressUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.virtual_network._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
        )
        args_schema.ip_address._nullable = False
        args_schema.frontend_ip_address._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        virtual_network = args.virtual_network.to_serialized_data()
        subnet = args.subnet.to_serialized_data()
        if subnet and not is_valid_resource_id(subnet):
            if not virtual_network:
                raise ArgumentUsageError(
                    "vnet name or vnet ID is required when using subnet name only."
                )
            # convert subnet name to subnet id
            subnet = f"{virtual_network}/subnets/{subnet}"
            args.subnet = subnet

    def post_instance_update(self, instance):
        if not has_value(instance.properties.virtual_network.id):
            instance.properties.virtual_network = None
        if not has_value(instance.properties.subnet.id):
            instance.properties.subnet = None

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class LBAddressPoolTunnelInterfaceAdd(_LBAddressPoolTunnelInterfaceAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.identifier._required = True
        args_schema.type._required = True
        args_schema.protocol._required = True
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class LBAddressPoolTunnelInterfaceUpdate(_LBAddressPoolTunnelInterfaceUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.identifier._nullable = False
        args_schema.type._nullable = False
        args_schema.protocol._nullable = False
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class LBProbeCreate(_LBProbeCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.port._required = True
        args_schema.protocol._required = True
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.number_of_probes):
            logger.warning(
                "The property \"numberOfProbes\" is not respected. Load Balancer health probes will probe up or down "
                "immediately after one probe regardless of the property's configured value. To control the number of "
                "successful or failed consecutive probes necessary to mark backend instances as healthy or unhealthy, "
                "please leverage the property \"probeThreshold\" instead."
            )
        if has_value(args.request_path) and args.request_path == "":
            args.request_path = None


class LBProbeUpdate(_LBProbeUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.port._nullable = False
        args_schema.protocol._nullable = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.number_of_probes):
            logger.warning(
                "The property \"numberOfProbes\" is not respected. Load Balancer health probes will probe up or down "
                "immediately after one probe regardless of the property's configured value. To control the number of "
                "successful or failed consecutive probes necessary to mark backend instances as healthy or unhealthy, "
                "please leverage the property \"probeThreshold\" instead."
            )
        if has_value(args.request_path) and args.request_path == "":
            args.request_path = None


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
        args_schema.idle_timeout_in_minutes._default = 4
        args_schema.enable_tcp_reset._default = False
        args_schema.protocol._required = True
        args_schema.frontend_port._required = True
        args_schema.backend_port._required = True
        args_schema.backend_address_pools._registered = False
        args_schema.disable_outbound_snat._registered = False   # it's not required for cross-region-lb
        args_schema.idle_timeout_in_minutes._registered = False
        args_schema.enable_tcp_reset._registered = False
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
            nullable=True,
            help="ID or name of the backend address pools. If only one exists, omit to use as default."
        )

        args_schema.protocol._nullable = False
        args_schema.frontend_port._nullable = False
        args_schema.backend_port._nullable = False
        args_schema.backend_address_pools._registered = False
        args_schema.disable_outbound_snat._registered = False   # it's not required for cross-region-lb
        args_schema.idle_timeout_in_minutes._registered = False
        args_schema.enable_tcp_reset._registered = False
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


@register_command("network cross-region-lb address-pool create")
class CrossRegionLoadBalancerAddressPoolCreate(_LBAddressPoolCreate):
    """Create load balancer backend address pool.

    :example: Create an address pool.
        az network cross-region-lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool

    :example: Create an address pool with several backend addresses using shorthand syntax arguments.
        az network cross-region-lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool --backend-addresses "[{name:addr1,frontend-ip-address:'/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb1'},{name:addr2,frontend-ip-address:'/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb2'}]"

    :example: Create an address pool with several backend addresses using config file
        az network cross-region-lb address-pool create -g MyResourceGroup --lb-name MyLb -n MyAddressPool --backend-addresses config_file.json
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
        args_schema.backend_addresses.Element.name._required = True
        args_schema.backend_addresses.Element.frontend_ip_address._required = True

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


@register_command("network cross-region-lb address-pool show")
class CrossRegionLoadBalancerAddressPoolShow(_LBAddressPoolShow):
    """Get load balancer backend address pool.

    :example: Get the details of an address pool.
        az network cross-region-lb address-pool show -g MyResourceGroup --lb-name MyLb -n MyAddressPool
    """


@register_command("network cross-region-lb address-pool delete")
class CrossRegionLoadBalancerAddressPoolDelete(_LBAddressPoolDelete):
    """Delete the specified load balancer backend address pool.

    :example: Delete an address pool.
        az network cross-region-lb address-pool delete -g MyResourceGroup --lb-name MyLb -n MyAddressPool
    """


@register_command("network cross-region-lb address-pool list")
class CrossRegionLoadBalancerAddressPoolList(_LBAddressPoolList):
    """List all the load balancer backed address pools.

    :example: List address pools.
        az network cross-region-lb address-pool list -g MyResourceGroup --lb-name MyLb -o table
    """


@register_command("network cross-region-lb address-pool address add")
class CrossRegionLoadBalancerAddressPoolAddressAdd(_LBAddressPoolAddressAdd):
    """Add one backend address into the load balance backend address pool.

    :example: Add one backend address into the load balance backend address pool.
        az network cross-region-lb address-pool address add -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress --frontend-ip-address /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/cli_test_lb_address_pool_addresses000001/providers/Microsoft.Network/loadBalancers/regional-lb/frontendIPConfigurations/fe-rlb2
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}"
        )

        args_schema.frontend_ip_address._required = True
        args_schema.ip_address._registered = False
        args_schema.subnet._registered = False
        args_schema.virtual_network._registered = False
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


@register_command("network cross-region-lb address-pool address remove")
class CrossRegionLoadBalancerAddressPoolAddressRemove(_LBAddressPoolAddressRemove):
    """Remove one backend address from the load balance backend address pool.
    :example: Remove one backend address from the load balance backend address pool.
        az network cross-region-lb address-pool address remove -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress
    """


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


@register_command("network cross-region-lb address-pool address list")
class CrossRegionLoadBalancerAddressPoolAddressList(_LBAddressPoolAddressList):
    """List all backend addresses of the load balance backend address pool.

    :example: List all backend addresses of the load balance backend address pool.
        az network cross-region-lb address-pool address list -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool
    """


@register_command("network cross-region-lb address-pool address show")
class CrossRegionLoadBalancerAddressPoolAddressShow(_LBAddressPoolAddressShow):
    """Show the backend address from the load balance backend address pool.

    :example: Show the backend address from the load balance backend address pool.
        az network cross-region-lb address-pool address show -g MyResourceGroup --lb-name MyLb --pool-name MyAddressPool -n MyAddress
    """
