# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.nic._update import Update as _NICUpdate


class NICUpdate(_NICUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_security_group = AAZResourceIdArg(
            options=["--network-security-group"],
            help="Name or ID of an existing network security group",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/networkSecurityGroups/{}",
            ),
            nullable=True,
        )
        args_schema.nsg._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.network_security_group):
            args.nsg.id = args.network_security_group
        if has_value(args.internal_dns_name) and args.internal_dns_name == "":
            args.internal_dns_name = None

    def post_instance_update(self, instance):
        if not has_value(instance.properties.network_security_group.id):
            instance.properties.network_security_group = None
