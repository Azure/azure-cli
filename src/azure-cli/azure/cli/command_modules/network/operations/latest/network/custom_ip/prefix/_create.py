# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.custom_ip.prefix._create import Create as _CustomIpPrefixCreate


class CustomIpPrefixCreate(_CustomIpPrefixCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.is_parent = AAZBoolArg(
            options=["--is-parent"],
            help="Denotes that resource is being created as a Parent CustomIpPrefix",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if args.is_parent:
            args.prefix_type = "Parent"
        elif has_value(args.cip_prefix_parent):
            args.prefix_type = "Child"
