# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.private_endpoint._create import Create as _PrivateEndpointCreate


class PrivateEndpointCreate(_PrivateEndpointCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg, AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.private_connection_resource_id = AAZStrArg(
            options=['--private-connection-resource-id'],
            help="The resource id of the private endpoint to connect to.",
            required=True)
        args_schema.group_ids = AAZListArg(
            options=["--group-ids", "--group-id"],
            help="The ID of the group obtained from the remote resource that this private endpoint should connect to. You can use \"az network private-link-resource list\" to obtain the supported group ids. You must provide this except for PrivateLinkService.,"
        )
        args_schema.group_ids.Element = AAZStrArg()
        args_schema.request_message = AAZStrArg(
            options=['--request-message'],
            help="A message passed to the owner of the remote resource with this connection request. Restricted to 140 chars.")
        args_schema.connection_name = AAZStrArg(
            options=['--connection-name'],
            help="Name of the private link service connection.",
            required=True)
        args_schema.manual_request = AAZBoolArg(
            options=['--manual-request'],
            help="Use manual request to establish the connection. Configure it as 'true' when you don't have access to the subscription of private link service.")
        args_schema.vnet_name = AAZStrArg(
            options=['--vnet-name'],
            help="The virtual network (VNet) associated with the subnet (Omit if supplying a subnet id).")
        args_schema.subnet = AAZResourceIdArg(
            options=['--subnet'],
            help="Name or ID of an existing subnet. If name specified, also specify --vnet-name. "
                 "If you want to use an existing subnet in other resource group or subscription, please provide the ID instead of the name of the subnet and do not specify the--vnet-name.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{}"
            )
        )
        args_schema.manual_private_link_service_connections._registered = False
        args_schema.private_link_service_connections._registered = False
        args_schema.edge_zone_type._registered = False
        args_schema.subnet_id._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        pls_connection = {'name': args.connection_name,
                          'group_ids': args.group_ids,
                          'request_message': args.request_message,
                          'private_link_service_id': args.private_connection_resource_id}

        if args.manual_request:
            args.manual_private_link_service_connections = [pls_connection]
        else:
            args.private_link_service_connections = [pls_connection]

        if has_value(args.subnet):
            args.subnet_id = args.subnet

        if has_value(args.edge_zone):
            args.edge_zone_type = 'EdgeZone'
