# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import register_command, AAZResourceIdArgFormat, has_value, AAZResourceIdArg, AAZStrArg
from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool._create import Create as _LBAddressPoolCreate
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool.basic._create import Create as _LBAddressPoolBasicCreate


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
