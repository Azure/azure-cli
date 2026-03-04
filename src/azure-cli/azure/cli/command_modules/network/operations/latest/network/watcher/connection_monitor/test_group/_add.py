# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.aaz import has_value, AAZResourceLocationArg, AAZListArg, AAZStrArg, AAZBoolArg, AAZFloatArg, AAZIntArg
from azure.cli.command_modules.network.aaz.latest.network.watcher.connection_monitor.test_group._add import Add as _WatcherConnectionMonitorTestGroupAdd
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_location


class WatcherConnectionMonitorTestGroupAdd(_WatcherConnectionMonitorTestGroupAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.destinations._registered = False
        args_schema.destinations._required = False
        args_schema.sources._registered = False
        args_schema.sources._required = False
        args_schema.test_configurations._registered = False
        args_schema.test_configurations._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        # V2 Endpoint
        args_schema.endpoint_dest_name = AAZStrArg(
            options=["--endpoint-dest-name"],
            help="The name of the destination of connection monitor endpoint. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            arg_group="V2 Endpoint",
            required=True
        )
        args_schema.endpoint_source_name = AAZStrArg(
            options=["--endpoint-source-name"],
            help="The name of the source of connection monitor endpoint. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            arg_group="V2 Endpoint",
            required=True
        )
        args_schema.endpoint_dest_address = AAZStrArg(
            options=["--endpoint-dest-address"],
            help="Address of the destination of connection monitor endpoint (IP or domain name)",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_dest_resource_id = AAZStrArg(
            options=["--endpoint-dest-resource-id"],
            help="Resource ID of the destination of connection monitor endpoint.",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_source_address = AAZStrArg(
            options=["--endpoint-source-address"],
            help="Address of the source of connection monitor endpoint (IP or domain name).",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_source_resource_id = AAZStrArg(
            options=["--endpoint-source-resource-id"],
            help="Resource ID of the source of connection monitor endpoint. "
                 "If endpoint is intended to used as source, this option is required.",
            arg_group="V2 Endpoint",
        )

        # V2 Test Configuration
        args_schema.test_config_name = AAZStrArg(
            options=["--test-config-name"],
            help="The name of the connection monitor test configuration. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            arg_group="V2 Test Configuration",
            required=True
        )
        args_schema.test_config_frequency = AAZStrArg(
            options=["--frequency"],
            help="The frequency of test evaluation, in seconds.  Default: 60.",
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_http_method = AAZStrArg(
            options=["--http-method"],
            help="The HTTP method to use.",
            arg_group="V2 Test Configuration",
            enum={"Get": "Get", "Post": "Post"},
        )
        args_schema.test_config_http_path = AAZStrArg(
            options=["--http-path"],
            help='The path component of the URI. For instance, "/dir1/dir2".',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_http_port = AAZIntArg(
            options=["--http-port"],
            help='The port to connect to.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_http_valid_status_codes = AAZListArg(
            options=["--http-valid-status-codes"],
            help="Space-separated list of HTTP status codes to consider successful. For instance, '2xx 301-304 418'",
            arg_group="V2 Test Configuration"
        )
        args_schema.test_config_http_valid_status_codes.Element = AAZStrArg()

        args_schema.test_config_http_prefer_https = AAZBoolArg(
            options=["--https-prefer"],
            help='Value indicating whether HTTPS is preferred over HTTP in cases where the choice is not explicit. '
                 ' Allowed values: false, true.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_icmp_disable_trace_route = AAZBoolArg(
            options=["--icmp-disable-trace-route"],
            help='Value indicating whether path evaluation with trace route should be disabled. false is default. '
                 ' Allowed values: false, true.',
            arg_group="V2 Test Configuration",
        )

        args_schema.test_config_preferred_ip_version = AAZStrArg(
            options=["--preferred-ip-version"],
            help='The preferred IP version to use in test evaluation. '
                 'The connection monitor may choose to use a different version depending on other parameters.',
            arg_group="V2 Test Configuration",
            enum={"IPv4": "IPv4", "IPv6": "IPv6"},
        )
        args_schema.test_config_protocol = AAZStrArg(
            options=["--protocol"],
            help='The protocol to use in test evaluation.',
            arg_group="V2 Test Configuration",
            enum={"Http": "Http", "Icmp": "Icmp", "Tcp": "Tcp"},
        )

        args_schema.test_config_tcp_disable_trace_route = AAZBoolArg(
            options=["--tcp-disable-trace-route"],
            help='Value indicating whether path evaluation with trace route should be disabled. false is default. '
                 'Allowed values: false, true.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_tcp_port = AAZIntArg(
            options=["--tcp-port"],
            help='The port to connect to.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_threshold_failed_percent = AAZIntArg(
            options=["--threshold-failed-percent"],
            help='The maximum percentage of failed checks permitted for a test to evaluate as successful.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_threshold_round_trip_time = AAZFloatArg(
            options=["--threshold-round-trip-time"],
            help='The maximum round-trip time in milliseconds permitted for a test to evaluate as successful.',
            arg_group="V2 Test Configuration",
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)

    # pylint: disable=too-many-boolean-expressions
    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance

        # deal with endpoint
        if has_value(args.endpoint_source_address) or has_value(args.endpoint_source_resource_id):
            src_endpoint = {
                "name": args.endpoint_source_name,
                "resource_id": args.endpoint_source_resource_id,
                "address": args.endpoint_source_address
            }
            instance.properties.endpoints.append(src_endpoint)
        if has_value(args.endpoint_dest_address) or has_value(args.endpoint_dest_resource_id):
            dst_endpoint = {
                "name": args.endpoint_dest_name,
                "resource_id": args.endpoint_dest_resource_id,
                "address": args.endpoint_dest_address
            }
            instance.properties.endpoints.append(dst_endpoint)

        args.sources.append(args.endpoint_source_name)
        args.destinations.append(args.endpoint_dest_name)

        # deal with test configuration
        if has_value(args.test_config_protocol) or has_value(args.test_config_preferred_ip_version) or \
                has_value(args.test_config_threshold_failed_percent) or \
                has_value(args.test_config_threshold_round_trip_time) or \
                has_value(args.test_config_tcp_disable_trace_route) or has_value(args.test_config_tcp_port) or \
                has_value(args.test_config_icmp_disable_trace_route) or \
                has_value(args.test_config_http_port) or has_value(args.test_config_http_method) or \
                has_value(args.test_config_http_path) or has_value(args.test_config_http_valid_status_codes) or \
                has_value(args.test_config_http_prefer_https):
            test_config = {
                "name": args.test_config_name,
                "test_frequency_sec": args.test_config_frequency,
                "protocol": args.test_config_protocol,
                "preferred_ip_version": args.test_config_preferred_ip_version,
            }
            if has_value(args.test_config_threshold_failed_percent) or \
                    has_value(args.test_config_threshold_round_trip_time):
                test_config['success_threshold'] = {
                    "checks_failed_percent": args.test_config_threshold_failed_percent,
                    "round_trip_time_ms": args.test_config_threshold_round_trip_time
                }
            if args.test_config_protocol == "Tcp":
                tcp_config = {
                    "port": args.test_config_tcp_port,
                    "disable_trace_route": args.test_config_tcp_disable_trace_route,
                }
                test_config['tcp_configuration'] = tcp_config
            elif args.test_config_protocol == "Icmp":
                icmp_config = {"disable_trace_route": args.test_config_icmp_disable_trace_route}
                test_config['icmp_configuration'] = icmp_config
            elif args.test_config_protocol == "Http":
                http_config = {
                    "port": args.test_config_http_port,
                    "method": args.test_config_http_method,
                    "path": args.test_config_http_path,
                    "valid_status_code_ranges": args.test_config_http_valid_status_codes,
                    "prefer_https": args.test_config_http_prefer_https,
                }
                test_config['http_configuration'] = http_config
            else:
                raise ValidationError('Unsupported protocol: "{}" for test configuration'.format(
                    args.test_config_protocol))
            instance.properties.test_configurations.append(test_config)
        args.test_configurations.append(args.test_config_name)
