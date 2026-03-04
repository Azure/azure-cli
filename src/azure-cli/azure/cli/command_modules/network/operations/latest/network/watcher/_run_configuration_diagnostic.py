# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.mgmt.core.tools import is_valid_resource_id, resource_id
from azure.cli.core.azclierror import ValidationError
from azure.cli.core.aaz import has_value, AAZResourceLocationArg, AAZStrArg
from azure.cli.command_modules.network.aaz.latest.network.watcher._run_configuration_diagnostic import RunConfigurationDiagnostic as _RunConfigurationDiagnostic
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_resource


class RunConfigurationDiagnostic(_RunConfigurationDiagnostic):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        args_schema.destination = AAZStrArg(
            options=["--destination"],
            arg_group="Query",
            help="Traffic destination. Accepted values are '*', IP address/CIDR, or Service Tag.",
        )
        args_schema.direction = AAZStrArg(
            options=["--direction"],
            arg_group="Query",
            help="Direction of the traffic.",
            enum={"Inbound": "Inbound", "Outbound": "Outbound"},
        )
        args_schema.port = AAZStrArg(
            options=["--port"],
            arg_group="Query",
            help="Traffic destination port. Accepted values are '*', port number (3389) or port range (80-100).",
        )
        args_schema.protocol = AAZStrArg(
            options=["--protocol"],
            arg_group="Query",
            help="Protocol to be verified on.",
            enum={"TCP": "TCP", "UDP": "UDP"},
        )
        args_schema.source = AAZStrArg(
            options=["--source"],
            arg_group="Query",
            help="Traffic source. Accepted values are '*', IP address/CIDR, or Service Tag.",
        )
        args_schema.parent = AAZStrArg(
            options=["--parent"],
            arg_group="Target",
            help="Parent path, e.g., virtualMachineScaleSets/vmss1.",
        )
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            arg_group="Target",
            help="Name of the resource group the target resource is in.",
        )
        args_schema.resource_type = AAZStrArg(
            options=["-t", "--resource-type"],
            arg_group="Target",
            help="Resource type.",
            enum={
                "applicationGateways": "applicationGateways",
                "networkInterfaces": "networkInterfaces",
                "virtualMachines": "virtualMachines",
            },
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        args_schema.queries._required = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # validate target resource
        resource_usage = ValidationError("usage error: --resource ID | --resource NAME --resource-type TYPE --resource-group NAME [--parent PATH]")
        # omit --parent since it is optional
        id_params = [has_value(args.resource_group_name), has_value(args.resource_type)]
        if not is_valid_resource_id(args.resource.to_serialized_data()):
            if not all(id_params):
                raise resource_usage
            # infer resource namespace
            NAMESPACES = {
                "virtualMachines": "Microsoft.Compute",
                "applicationGateways": "Microsoft.Network",
                "networkInterfaces": "Microsoft.Network",
            }
            resource_namespace = NAMESPACES[args.resource_type.to_serialized_data()]
            if has_value(args.parent):
                # special case for virtualMachineScaleSets/NetworkInterfaces, since it is
                # the only one to need `--parent`
                resource_namespace = "Microsoft.Compute"
            args.resource = resource_id(
                subscription=self.ctx.subscription_id,
                resource_group=args.resource_group_name,
                namespace=resource_namespace,
                type=args.resource_type,
                parent=args.parent,
                name=args.resource
            )
        elif any(id_params) or has_value(args.parent):
            raise resource_usage
        # validate query
        query_usage = ValidationError("usage error: --queries JSON | --destination DEST --source SRC --direction DIR --port PORT --protocol PROTOCOL")
        query_params = [has_value(args.destination), has_value(args.port), has_value(args.direction), has_value(args.protocol), has_value(args.source)]
        if has_value(args.queries):
            if any(query_params):
                raise query_usage
        elif not all(query_params):
            raise query_usage
        else:
            args.queries = [{
                "destination": args.destination,
                "destination_port": args.port,
                "direction": args.direction,
                "protocol": args.protocol,
                "source": args.source
            }]

        get_network_watcher_from_resource(self)
