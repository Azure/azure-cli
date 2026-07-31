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
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat, AAZStrArg
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
        args_schema.pip_addresses_v6_input = AAZListArg(
            options=["--pip-addresses-v6"],
            help="Space-separated list of public IPv6 addresses (Names or IDs).",
        )
        args_schema.pip_addresses_v6_input.Element = AAZStrArg()
        args_schema.pip_prefixes_v6_input = AAZListArg(
            options=["--pip-prefixes-v6"],
            help="Space-separated list of public IPv6 prefixes (Names or IDs).",
        )
        args_schema.pip_prefixes_v6_input.Element = AAZStrArg()
        args_schema.pip_addresses._registered = False
        args_schema.pip_prefixes._registered = False
        args_schema.pip_addrs_v6._registered = False
        args_schema.pip_prefs_v6._registered = False
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

        from azure.cli.core.aaz import has_value
        from azure.cli.core.util import shell_safe_json_parse

        sub = self.ctx.subscription_id
        rg = args.resource_group.to_serialized_data()

        # ---------- v6 addresses ----------
        if has_value(args.pip_addresses_v6_input):
            serialized = args.pip_addresses_v6_input.to_serialized_data() or []

            # legacy JSON string --pip-addresses-v6 "[{'id':'/.../id'}]"
            if len(serialized) == 1 and isinstance(serialized[0], str) and serialized[0].lstrip().startswith('['):
                parsed = shell_safe_json_parse(serialized[0])
                ids = [it.get("id") for it in parsed if isinstance(it, dict) and it.get("id")]
                args.pip_addrs_v6 = [{"id": rid} for rid in ids]
            else:
                args.pip_addrs_v6 = assign_aaz_list_arg(
                    args.pip_addrs_v6,
                    args.pip_addresses_v6_input,
                    element_transformer=lambda _, v: {
                        "id": v if str(v).strip().startswith("/")
                        else f"/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network"
                             f"/publicIPAddresses/{str(v).strip()}"
                    }
                )

        # ---------- v6 prefixes ----------
        if has_value(args.pip_prefixes_v6_input):
            serialized = args.pip_prefixes_v6_input.to_serialized_data() or []

            # legacy JSON string --pip-prefixes-v6 "[{'id':'/.../id'}]"
            if len(serialized) == 1 and isinstance(serialized[0], str) and serialized[0].lstrip().startswith('['):
                parsed = shell_safe_json_parse(serialized[0])
                ids = [it.get("id") for it in parsed if isinstance(it, dict) and it.get("id")]
                args.pip_prefs_v6 = [{"id": rid} for rid in ids]
            else:
                args.pip_prefs_v6 = assign_aaz_list_arg(
                    args.pip_prefs_v6,
                    args.pip_prefixes_v6_input,
                    element_transformer=lambda _, v: {
                        "id": v if str(v).strip().startswith("/")
                        else f"/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network"
                             f"/publicIPPrefixes/{str(v).strip()}"
                    }
                )

        args.sku.name = "Standard"


class GatewayUpdate(_GatewayUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat, AAZStrArg
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
        args_schema.pip_addresses_v6_input = AAZListArg(
            options=["--pip-addresses-v6"],
            help="Space-separated list of public IPv6 addresses (Names or IDs).",
            nullable=True,
        )
        args_schema.pip_addresses_v6_input.Element = AAZStrArg(nullable=True)
        args_schema.pip_prefixes_v6_input = AAZListArg(
            options=["--pip-prefixes-v6"],
            help="Space-separated list of public IPv6 prefixes (Names or IDs).",
            nullable=True,
        )
        args_schema.pip_prefixes_v6_input.Element = AAZStrArg(nullable=True)
        args_schema.pip_addresses._registered = False
        args_schema.pip_prefixes._registered = False
        args_schema.pip_addrs_v6._registered = False
        args_schema.pip_prefs_v6._registered = False
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

        from azure.cli.core.aaz import has_value
        from azure.cli.core.util import shell_safe_json_parse

        sub = self.ctx.subscription_id
        rg = args.resource_group.to_serialized_data()

        # ---------- v6 addresses ----------
        if has_value(args.pip_addresses_v6_input):
            serialized = args.pip_addresses_v6_input.to_serialized_data() or []

            # legacy JSON string --pip-addresses-v6 "[{'id':'/.../id'}]"
            if len(serialized) == 1 and isinstance(serialized[0], str) and serialized[0].lstrip().startswith('['):
                parsed = shell_safe_json_parse(serialized[0])
                ids = [it.get("id") for it in parsed if isinstance(it, dict) and it.get("id")]
                args.pip_addrs_v6 = [{"id": rid} for rid in ids]
            else:
                args.pip_addrs_v6 = assign_aaz_list_arg(
                    args.pip_addrs_v6,
                    args.pip_addresses_v6_input,
                    element_transformer=lambda _, v: {
                        "id": v if str(v).strip().startswith("/")
                        else f"/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network"
                             f"/publicIPAddresses/{str(v).strip()}"
                    }
                )

        # ---------- v6 prefixes ----------
        if has_value(args.pip_prefixes_v6_input):
            serialized = args.pip_prefixes_v6_input.to_serialized_data() or []

            # legacy JSON string --pip-prefixes-v6 "[{'id':'/.../id'}]"
            if len(serialized) == 1 and isinstance(serialized[0], str) and serialized[0].lstrip().startswith('['):
                parsed = shell_safe_json_parse(serialized[0])
                ids = [it.get("id") for it in parsed if isinstance(it, dict) and it.get("id")]
                args.pip_prefs_v6 = [{"id": rid} for rid in ids]
            else:
                args.pip_prefs_v6 = assign_aaz_list_arg(
                    args.pip_prefs_v6,
                    args.pip_prefixes_v6_input,
                    element_transformer=lambda _, v: {
                        "id": v if str(v).strip().startswith("/")
                        else f"/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network"
                             f"/publicIPPrefixes/{str(v).strip()}"
                    }
                )
