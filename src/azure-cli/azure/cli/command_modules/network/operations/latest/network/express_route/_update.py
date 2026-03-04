# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.express_route._update import Update as _ExpressRouteUpdate


def _validate_bandwidth(bandwidth, mbps=True):
    from azure.cli.core.azclierror import InvalidArgumentValueError

    unit = 'mbps' if mbps else 'gbps'
    if bandwidth is None:
        return
    if len(bandwidth) == 1:
        bandwidth_comps = bandwidth[0].to_serialized_data().split(' ')
    else:
        bandwidth_comps = bandwidth.to_serialized_data()

    usage_error = InvalidArgumentValueError('--bandwidth INT {Mbps,Gbps}')
    if len(bandwidth_comps) == 1:
        bandwidth_comps.append(unit)
    if len(bandwidth_comps) > 2:
        raise usage_error
    input_value = bandwidth_comps[0]
    input_unit = bandwidth_comps[1].lower()
    if float(input_value) and input_unit in ['mbps', 'gbps']:
        if input_unit == unit:
            converted_bandwidth = float(bandwidth_comps[0])
        elif input_unit == 'gbps':
            converted_bandwidth = float(bandwidth_comps[0]) * 1000
        else:
            converted_bandwidth = float(bandwidth_comps[0]) / 1000
    else:
        raise usage_error
    return converted_bandwidth


class ExpressRouteUpdate(_ExpressRouteUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.bandwidth = AAZListArg(
            options=["--bandwidth"],
            help="Bandwidth of the circuit. Usage: INT {Mbps,Gbps}. Defaults to Mbps.",
            nullable=True
        )
        args_schema.bandwidth.Element = AAZStrArg(nullable=True)
        args_schema.bandwidth_in_mbps._registered = False
        args_schema.bandwidth_in_gbps._registered = False
        args_schema.sku_name._registered = False
        args_schema.express_route_port._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/expressRoutePorts/{}"
        )

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.sku_tier) and has_value(args.sku_family):
            args.sku_name = f"{args.sku_tier}_{args.sku_family}"

        if has_value(args.bandwidth):
            converted_bandwidth = _validate_bandwidth(args.bandwidth)
            args.bandwidth_in_gbps = converted_bandwidth / 1000
            args.bandwidth_in_mbps = int(converted_bandwidth)

    def post_instance_update(self, instance):
        if not has_value(instance.properties.express_route_port.id):
            instance.properties.express_route_port = None

        if has_value(instance.properties.express_route_port):
            instance.properties.service_provider_properties = None
        else:
            instance.properties.bandwidth_in_gbps = None
