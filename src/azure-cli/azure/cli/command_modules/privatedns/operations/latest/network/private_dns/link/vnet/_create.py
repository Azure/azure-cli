# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
from azure.cli.command_modules.privatedns.aaz.latest.network.private_dns.link.vnet._create import (
    Create as _PrivateDNSLinkVNetCreate
)


class PrivateDNSLinkVNetCreate(_PrivateDNSLinkVNetCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.virtual_network._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/virtualNetworks/{}"
        )
        args_schema.registration_enabled._required = True
        args_schema.virtual_network._required = True
        args_schema.if_none_match._registered = False
        args_schema.location._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.location = "global"
        args.if_none_match = "*"
