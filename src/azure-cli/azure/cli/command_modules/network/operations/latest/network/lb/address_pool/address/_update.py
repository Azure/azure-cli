# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import AAZResourceIdArgFormat, has_value
from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool.address._update import Update as _LBAddressPoolAddressUpdate


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
