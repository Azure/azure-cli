# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.aaz.utils import assign_aaz_list_arg

from ..aaz.latest.network.nat.gateway import Create as _GatewayCreate, Update as _GatewayUpdate


class GatewayCreate(_GatewayCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_addresses = AAZListArg(
            options=["--public-ip-addresses"],
            help="Space-separated list of public IP addresses (Names or IDs).",
        )
        args_schema.public_ip_addresses.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/publicIPAddresses/{}",
            ),
        )
        args_schema.public_ip_prefixes = AAZListArg(
            options=["--public-ip-prefixes"],
            help="Space-separated list of public IP prefixes (Names or IDs).",
        )
        args_schema.public_ip_prefixes.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/publicIPPrefixes/{}",
            ),
        )
        args_schema.pip_addresses._registered = False
        args_schema.pip_prefixes._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.pip_addresses = assign_aaz_list_arg(
            args.pip_addresses,
            args.public_ip_addresses,
            element_transformer=lambda _, address_id: {"id": address_id}
        )
        args.pip_prefixes = assign_aaz_list_arg(
            args.pip_prefixes,
            args.public_ip_prefixes,
            element_transformer=lambda _, prefix_id: {"id": prefix_id}
        )
        args.sku.name = "Standard"


class GatewayUpdate(_GatewayUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_addresses = AAZListArg(
            options=["--public-ip-addresses"],
            help="Space-separated list of public IP addresses (Names or IDs).",
            nullable=True,
        )
        args_schema.public_ip_addresses.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/publicIPAddresses/{}",
            ),
            nullable=True,
        )
        args_schema.public_ip_prefixes = AAZListArg(
            options=["--public-ip-prefixes"],
            help="Space-separated list of public IP prefixes (Names or IDs).",
            nullable=True,
        )
        args_schema.public_ip_prefixes.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/publicIPPrefixes/{}",
            ),
            nullable=True,
        )
        args_schema.pip_addresses._registered = False
        args_schema.pip_prefixes._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.pip_addresses = assign_aaz_list_arg(
            args.pip_addresses,
            args.public_ip_addresses,
            element_transformer=lambda _, address_id: {"id": address_id}
        )
        args.pip_prefixes = assign_aaz_list_arg(
            args.pip_prefixes,
            args.public_ip_prefixes,
            element_transformer=lambda _, prefix_id: {"id": prefix_id}
        )
