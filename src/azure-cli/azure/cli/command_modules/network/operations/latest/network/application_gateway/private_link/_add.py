# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id, resource_id
from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import ValidationError
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.private_link._add import Add as _AGPrivateLinkAdd


class AGPrivateLinkAdd(_AGPrivateLinkAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZBoolArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip = AAZStrArg(
            options=["--frontend-ip"],
            help="Frontend IP that the private link will associate to.",
            required=True,
        )
        args_schema.subnet = AAZStrArg(
            options=["--subnet"],
            help="Name or ID of a subnet within the same vnet of an application gateway.",
            arg_group="Properties",
            required=True,
        )
        args_schema.subnet_prefix = AAZStrArg(
            options=["--subnet-prefix"],
            help="CIDR prefix to use when creating a new subnet.",
            arg_group="Properties",
        )
        args_schema.ip_address = AAZStrArg(
            options=["--ip-address"],
            help="Static private IP address of a subnet for private link. If omitting, a dynamic one will be created.",
            arg_group="Properties",
        )
        args_schema.primary = AAZBoolArg(
            options=["--primary"],
            help="Whether the IP configuration is primary or not.",
            arg_group="Properties",
        )
        args_schema.ip_configurations._registered = False
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if not any(fic for fic in instance.properties.frontend_ip_configurations if fic.name == args.frontend_ip):
            err_msg = "Frontend IP doesn't exist."
            raise ValidationError(err_msg)

        private_link_id = resource_id(
            subscription=self.ctx.subscription_id,
            resource_group=args.resource_group,
            namespace="Microsoft.Network",
            type="applicationGateways",
            name=args.gateway_name,
            child_type_1="privateLinkConfigurations",
            child_name_1=args.name
        )
        for fic in instance.properties.frontend_ip_configurations:
            if has_value(fic.properties.private_link_configuration) \
                    and fic.properties.private_link_configuration.id == private_link_id:
                err_msg = "Frontend IP already reference an existing private link."
                raise ValidationError(err_msg)
        # associate private link with frontend IP configuration
        for fic in instance.properties.frontend_ip_configurations:
            if fic.name == args.frontend_ip:
                fic.properties.private_link_configuration = {"id": private_link_id}

        if has_value(instance.properties.private_link_configurations):
            for plc in instance.properties.private_link_configurations:
                if plc.name == args.name:
                    err_msg = "Private link name duplicates."
                    raise ValidationError(err_msg)
        # prepare subnet for new private link
        rid = instance.properties.gateway_ip_configurations[0].properties.subnet.id.to_serialized_data()
        metadata = parse_resource_id(rid)
        if not is_valid_resource_id(args.subnet.to_serialized_data()):
            args.subnet = resource_id(
                subscription=metadata["subscription"],
                resource_group=metadata["resource_group"],
                namespace="Microsoft.Network",
                type="virtualNetworks",
                name=metadata["name"],
                child_type_1="subnets",
                child_name_1=args.subnet
            )

        from azure.cli.command_modules.network.aaz.latest.network.vnet._show import Show
        vnet = Show(cli_ctx=self.cli_ctx)(command_args={
            "name": metadata["name"],
            "resource_group": metadata["resource_group"]
        })
        for subnet in vnet["subnets"]:
            if subnet["id"] == args.subnet:
                break
        else:
            subnet_name = parse_resource_id(args.subnet.to_serialized_data())["child_name_1"]

            from azure.cli.core.commands import LongRunningOperation
            from azure.cli.command_modules.network.aaz.latest.network.vnet.subnet._create import Create as VNetSubnetCreate
            poller = VNetSubnetCreate(cli_ctx=self.cli_ctx)(command_args={
                "name": subnet_name,
                "vnet_name": metadata["name"],
                "resource_group": metadata["resource_group"],
                "address_prefix": args.subnet_prefix,
                "private_link_service_network_policies": "Disabled"
            })
            LongRunningOperation(self.cli_ctx)(poller)

        args.ip_configurations = [{
            "name": "PrivateLinkDefaultIPConfiguration",
            "private_ip_address": args.ip_address,
            "private_ip_allocation_method": "Static" if has_value(args.ip_address) else "Dynamic",
            "subnet": {"id": args.subnet},
            "primary": args.primary
        }]
