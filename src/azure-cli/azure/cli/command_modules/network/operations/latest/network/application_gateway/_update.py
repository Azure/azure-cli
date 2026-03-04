# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.custom import _is_v2_sku
from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.application_gateway._update import Update as _ApplicationGatewayUpdate


class ApplicationGatewayUpdate(_ApplicationGatewayUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZDictArg, AAZStrArg, AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.custom_error_pages = AAZDictArg(
            options=["--custom-error-pages"],
            help="Space-separated list of custom error pages in `STATUS_CODE=URL` format.",
            nullable=True,
        )
        args_schema.custom_error_pages.Element = AAZStrArg(
            nullable=True,
        )
        args_schema.http2.enum = AAZArgEnum({"Enabled": True, "Disabled": False})
        args_schema.custom_error_configurations._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.custom_error_pages):
            configurations = []
            for code, url in args.custom_error_pages.items():
                configurations.append({
                    "status_code": code,
                    "custom_error_page_url": url,
                })
            args.custom_error_configurations = configurations
        if has_value(args.sku):
            sku = str(args.sku)
            args.sku.tier = sku.split("_", 1)[0] if not _is_v2_sku(sku) else sku
