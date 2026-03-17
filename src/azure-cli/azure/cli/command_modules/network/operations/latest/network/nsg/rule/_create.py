# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.nsg.rule._create import Create as _NSGRuleCreate
from azure.cli.command_modules.network.custom import _handle_plural_or_singular


class NSGRuleCreate(_NSGRuleCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.priority._required = True
        args_schema.destination_asgs = AAZListArg(
            options=["--destination-asgs"],
            arg_group="Destination",
            help="Space-separated list of application security group names or IDs. Limited by backend server, "
                 "temporarily this argument only supports one application security group name or ID.",
        )
        args_schema.destination_asgs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
        )
        args_schema.source_asgs = AAZListArg(
            options=["--source-asgs"],
            arg_group="Source",
            help="Space-separated list of application security group names or IDs. Limited by backend server, "
                 "temporarily this argument only supports one application security group name or ID.",
        )
        args_schema.source_asgs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
        )
        # filter arguments
        args_schema.destination_address_prefix._registered = False
        args_schema.destination_application_security_groups._registered = False
        args_schema.destination_port_range._registered = False
        args_schema.source_address_prefix._registered = False
        args_schema.source_application_security_groups._registered = False
        args_schema.source_port_range._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        _handle_plural_or_singular(args, "destination_address_prefixes", "destination_address_prefix")
        _handle_plural_or_singular(args, "destination_port_ranges", "destination_port_range")
        _handle_plural_or_singular(args, "source_address_prefixes", "source_address_prefix")
        _handle_plural_or_singular(args, "source_port_ranges", "source_port_range")
        # handle application security groups
        if has_value(args.destination_asgs):
            args.destination_application_security_groups = [{"id": asg_id} for asg_id in args.destination_asgs]
            if has_value(args.destination_address_prefix):
                args.destination_address_prefix = None
        if has_value(args.source_asgs):
            args.source_application_security_groups = [{"id": asg_id} for asg_id in args.source_asgs]
            if has_value(args.source_address_prefix):
                args.source_address_prefix = None
