# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.public_ip.prefix._create import Create as _PublicIpPrefixCreate


class PublicIpPrefixCreate(_PublicIpPrefixCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZDictArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.custom_ip_prefix_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/customIPPrefixes/{}"
        )
        args_schema.ip_tags = AAZDictArg(
            options=["--ip-tags"],
            help="The list of tags associated with the public IP prefix in 'TYPE=VAL' format.",
        )
        args_schema.ip_tags.Element = AAZStrArg()
        args_schema.type._registered = False
        args_schema.ip_tags_list._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.edge_zone):
            args.type = 'EdgeZone'
        if has_value(args.ip_tags):
            ip_tags = []
            for k, v in args.ip_tags.to_serialized_data().items():
                ip_tags.append({"ip_tag_type": k, "tag": v})
            args.ip_tags_list = ip_tags
