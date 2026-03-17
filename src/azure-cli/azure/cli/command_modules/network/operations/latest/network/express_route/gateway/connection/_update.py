# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.command_modules.network.aaz.latest.network.express_route.gateway.connection._update import Update as _ExpressRouteConnectionUpdate


class ExpressRouteConnectionUpdate(_ExpressRouteConnectionUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.associated_route_table = AAZStrArg(
            options=['--associated-route-table', '--associated'],
            arg_group="Routing Configuration",
            help="The resource id of route table associated with this routing configuration.",
            is_preview=True,
            nullable=True)
        args_schema.propagated_route_tables = AAZListArg(
            options=['--propagated-route-tables', '--propagated'],
            arg_group="Routing Configuration",
            help="Space-separated list of resource id of propagated route tables.",
            is_preview=True,
            nullable=True)
        args_schema.propagated_route_tables.Element = AAZStrArg(nullable=True)
        args_schema.circuit_name = AAZStrArg(
            options=['--circuit-name'],
            arg_group="Peering",
            help="ExpressRoute circuit name.",
            nullable=True
        )
        args_schema.peering._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/expressRouteCircuits/{circuit_name}/peerings/{}"
        )
        args_schema.associated_id._registered = False
        args_schema.propagated_ids._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if has_value(args.associated_route_table):
            args.associated_id = {"id": args.associated_route_table}

        args.propagated_ids = assign_aaz_list_arg(
            args.propagated_ids,
            args.propagated_route_tables,
            element_transformer=lambda _, propagated_route_table: {"id": propagated_route_table}
        )
