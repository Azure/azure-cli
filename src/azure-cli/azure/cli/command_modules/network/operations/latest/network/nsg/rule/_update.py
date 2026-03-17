# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.command_modules.network.aaz.latest.network.nsg.rule._update import Update as _NSGRuleUpdate


class NSGRuleUpdate(_NSGRuleUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.destination_asgs = AAZListArg(
            options=["--destination-asgs"],
            arg_group="Destination",
            help="Space-separated list of application security group names or IDs. Limited by backend server, "
                 "temporarily this argument only supports one application security group name or ID.",
            nullable=True,
        )
        args_schema.destination_asgs.Element = AAZResourceIdArg(
            nullable=True,
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
            nullable=True,
        )
        args_schema.source_asgs.Element = AAZResourceIdArg(
            nullable=True,
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
        # handle application security groups
        args.destination_application_security_groups = assign_aaz_list_arg(
            args.destination_application_security_groups,
            args.destination_asgs,
            element_transformer=lambda _, asg_id: {"id": asg_id}
        )
        args.source_application_security_groups = assign_aaz_list_arg(
            args.source_application_security_groups,
            args.source_asgs,
            element_transformer=lambda _, asg_id: {"id": asg_id}
        )

    def pre_instance_update(self, instance):
        if instance.properties.sourceAddressPrefix:
            instance.properties.sourceAddressPrefixes = [instance.properties.sourceAddressPrefix]
            instance.properties.sourceAddressPrefix = None
        if instance.properties.destinationAddressPrefix:
            instance.properties.destinationAddressPrefixes = [instance.properties.destinationAddressPrefix]
            instance.properties.destinationAddressPrefix = None
        if instance.properties.sourcePortRange:
            instance.properties.sourcePortRanges = [instance.properties.sourcePortRange]
            instance.properties.sourcePortRange = None
        if instance.properties.destinationPortRange:
            instance.properties.destinationPortRanges = [instance.properties.destinationPortRange]
            instance.properties.destinationPortRange = None

    def post_instance_update(self, instance):
        if instance.properties.sourceAddressPrefixes and len(instance.properties.sourceAddressPrefixes) == 1:
            instance.properties.sourceAddressPrefix = instance.properties.sourceAddressPrefixes[0]
            instance.properties.sourceAddressPrefixes = None
        if instance.properties.destinationAddressPrefixes and len(instance.properties.destinationAddressPrefixes) == 1:
            instance.properties.destinationAddressPrefix = instance.properties.destinationAddressPrefixes[0]
            instance.properties.destinationAddressPrefixes = None
        if instance.properties.sourcePortRanges and len(instance.properties.sourcePortRanges) == 1:
            instance.properties.sourcePortRange = instance.properties.sourcePortRanges[0]
            instance.properties.sourcePortRanges = None
        if instance.properties.destinationPortRanges and len(instance.properties.destinationPortRanges) == 1:
            instance.properties.destinationPortRange = instance.properties.destinationPortRanges[0]
            instance.properties.destinationPortRanges = None
