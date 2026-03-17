# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from knack.util import CLIError
from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.core.azclierror import RequiredArgumentMissingError, MutuallyExclusiveArgumentError
from azure.cli.core.commands.arm import get_arm_resource_by_id
from azure.cli.core.aaz import has_value, AAZBoolArg, AAZIntArg, AAZIntArgFormat, AAZResourceIdArg, AAZResourceIdArgFormat
from azure.cli.command_modules.network._validators import validate_managed_identity_resource_id
from azure.cli.command_modules.network.aaz.latest.network.watcher.flow_log._create import Create as _NwFlowLogCreate
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_location


class NwFlowLogCreate(_NwFlowLogCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group._required = False
        args_schema.location._required = True
        args_schema.flow_analytics_configuration._registered = False
        args_schema.retention_policy._registered = False
        args_schema.target_resource_id._registered = False
        args_schema.traffic_analytics_interval = AAZIntArg(
            options=['--interval'], arg_group="Traffic Analytics",
            help="Interval in minutes at which to conduct flow analytics. Temporarily allowed values are 10 and 60.",
            default=60,
            fmt=AAZIntArgFormat(
                maximum=60,
                minimum=10,
            )
        )
        args_schema.user_assigned_identity = AAZResourceIdArg(
            options=["--user-assigned-identity"],
            help="Name or ID of the ManagedIdentity Resource.",
            required=False,
        )
        args_schema.retention = AAZIntArg(
            options=['--retention'],
            help="Number of days to retain logs.",
        )
        args_schema.traffic_analytics_enabled = AAZBoolArg(
            options=['--traffic-analytics'], arg_group="Traffic Analytics",
            help="Enable traffic analytics. Defaults to true if `--workspace` is provided."
        )
        args_schema.traffic_analytics_workspace = AAZResourceIdArg(
            options=['--workspace'], arg_group="Traffic Analytics",
            help="Name or ID of a Log Analytics workspace. Must be in the same region of flow log",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.OperationalInsights/workspaces/{}"
            )
        )
        args_schema.vnet = AAZResourceIdArg(
            options=['--vnet'],
            help="Name or ID of the Virtual Network Resource.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
            )
        )
        args_schema.subnet = AAZResourceIdArg(
            options=['--subnet'],
            help="Name or ID of Subnet.",
        )
        args_schema.nic = AAZResourceIdArg(
            options=['--nic'],
            help="Name or ID of the Network Interface (NIC) Resource.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/networkInterfaces/{}"
            )
        )
        args_schema.nsg = AAZResourceIdArg(
            options=['--nsg'],
            help="Name or ID of the network security group.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/networkSecurityGroups/{}"
            )
        )
        args_schema.storage_account._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{}"
        )

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group')
        if has_value(args.subnet):
            subnet = args.subnet.to_serialized_data()
            if not is_valid_resource_id(subnet) and has_value(args.vnet):
                args.subnet = args.vnet.to_serialized_data() + "/subnets/" + subnet

        if not has_value(args.enabled):
            args.enabled = True
        if sum(map(bool, [args.vnet, args.subnet, args.nic, args.nsg])) == 0:
            raise RequiredArgumentMissingError("Please enter atleast one target resource ID.")
        if sum(map(bool, [args.vnet, args.nic, args.nsg])) > 1:
            raise MutuallyExclusiveArgumentError("Please enter only one target resource ID.")

        if has_value(args.subnet):
            args.target_resource_id = args.subnet
        elif has_value(args.vnet) and not has_value(args.subnet):
            args.target_resource_id = args.vnet
        elif has_value(args.nic):
            args.target_resource_id = args.nic
        elif has_value(args.nsg):
            args.target_resource_id = args.nsg

        if has_value(args.user_assigned_identity):
            user_assigned_identity = args.user_assigned_identity.to_serialized_data()
            is_valid_miresource_id = validate_managed_identity_resource_id(user_assigned_identity)
            if not is_valid_miresource_id:
                raise CLIError('Managed Identity resource id is invalid')
            if user_assigned_identity.lower() != 'none':
                args.identity = {
                    "type": "UserAssigned",
                    "user_assigned_identities": {user_assigned_identity: {}}
                }
            else:
                args.identity = {
                    "type": "None"
                }

        if has_value(args.retention):
            if args.retention > 0:
                args.retention_policy = {"days": args.retention, "enabled": True}

        if has_value(args.traffic_analytics_workspace):

            workspace = get_arm_resource_by_id(self.cli_ctx, args.traffic_analytics_workspace.to_serialized_data())
            if not workspace:
                raise CLIError('Name or ID of workspace is invalid')

            args.flow_analytics_configuration = {"workspace_id": workspace.properties['customerId'],
                                                 "workspace_region": workspace.location,
                                                 "workspace_resource_id": workspace.id}
            if has_value(args.traffic_analytics_enabled):
                args.flow_analytics_configuration['enabled'] = args.traffic_analytics_enabled
            if has_value(args.traffic_analytics_interval):
                args.flow_analytics_configuration['traffic_analytics_interval'] = args.traffic_analytics_interval
