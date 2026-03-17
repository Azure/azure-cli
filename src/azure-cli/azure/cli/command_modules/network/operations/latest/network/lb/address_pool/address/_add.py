# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import AAZResourceIdArgFormat
from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool.address._add import Add as _LBAddressPoolAddressAdd


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
