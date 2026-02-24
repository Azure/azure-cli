# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import AAZClientConfiguration, has_value, register_client, AAZFileArgTextFormat
from azure.cli.command_modules.network.aaz.latest.network.express_route._create import Create as _ExpressRouteCreate


class ExpressRouteCreate(_ExpressRouteCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.bandwidth = AAZListArg(
            options=["--bandwidth"],
            help="Bandwidth of the circuit. Usage: INT {Mbps,Gbps}. Defaults to Mbps."
        )
        args_schema.bandwidth.Element = AAZStrArg()
        args_schema.bandwidth_in_mbps._registered = False
        args_schema.bandwidth_in_gbps._registered = False
        args_schema.sku_name._registered = False
        args_schema.express_route_port._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/expressRoutePorts/{}",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.bandwidth):
            converted_bandwidth = _validate_bandwidth(args.bandwidth)
        args.sku_name = '{}_{}'.format(args.sku_tier, args.sku_family)

        if has_value(args.express_route_port):
            args.provider = None
            args.peering_location = None
            args.bandwidth_in_gbps = converted_bandwidth / 1000.0
        else:
            args.bandwidth_in_mbps = int(converted_bandwidth)
