# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import AAZResourceIdArgFormat, has_value, AAZResourceIdArg, AAZStrArg
from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool._update import Update as _LBAddressPoolUpdate


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
