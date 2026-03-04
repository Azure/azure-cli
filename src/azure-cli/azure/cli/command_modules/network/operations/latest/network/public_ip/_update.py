# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.public_ip._update import Update as _PublicIPUpdate


class PublicIPUpdate(_PublicIPUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZDictArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_prefix._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/publicIPPrefixes/{}",
        )
        args_schema.ddos_protection_plan._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/ddosProtectionPlans/{}",
        )
        args_schema.ip_tags = AAZDictArg(
            options=["--ip-tags"],
            help="Space-separated list of IP tags in `TYPE=VAL` format.",
            nullable=True
        )
        args_schema.ip_tags.Element = AAZStrArg()
        args_schema.ip_tags_list._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.ip_tags):
            if (ip_tags := args.ip_tags.to_serialized_data()) is None:
                args.ip_tags_list = []
            else:
                args.ip_tags_list = [{"ip_tag_type": k, "tag": v} for k, v in ip_tags.items()]

    def post_instance_update(self, instance):
        if not has_value(instance.properties.ddos_settings.ddos_protection_plan.id):
            instance.properties.ddos_settings.ddos_protection_plan = None
