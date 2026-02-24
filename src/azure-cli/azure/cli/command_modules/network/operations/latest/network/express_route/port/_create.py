# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import AAZClientConfiguration, has_value, register_client, AAZFileArgTextFormat
from azure.cli.command_modules.network.aaz.latest.network.express_route.port._create import Create as _ExpressRoutePortCreate


class ExpressRoutePortCreate(_ExpressRoutePortCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.bandwidth = AAZListArg(
            options=["--bandwidth"],
            help="Bandwidth of the circuit. Usage: INT {Mbps,Gbps}. Defaults to Mbps."
        )
        args_schema.bandwidth.Element = AAZStrArg()
        args_schema.bandwidth_in_gbps._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.bandwidth):
            converted_bandwidth = _validate_bandwidth(args.bandwidth, mbps=False)
            args.bandwidth_in_gbps = int(converted_bandwidth)
