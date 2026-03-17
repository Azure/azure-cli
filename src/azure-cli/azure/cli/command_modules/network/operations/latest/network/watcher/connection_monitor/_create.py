# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.aaz import has_value, AAZListArg, AAZStrArg, AAZBoolArg, AAZFloatArg, AAZIntArg
from azure.cli.command_modules.network.aaz.latest.network.watcher.connection_monitor._create import Create as _WatcherConnectionMonitorCreate
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_location, process_nw_cm_v2_create_namespace


class WatcherConnectionMonitorCreate(_WatcherConnectionMonitorCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group._required = False

        args_schema.auto_start._registered = False
        args_schema.monitoring_interval_in_seconds._registered = False
        args_schema.source._registered = False
        args_schema.destination._registered = False
        args_schema.endpoints._registered = False
        args_schema.test_configurations._registered = False
        args_schema.test_groups._registered = False
        args_schema.outputs._registered = False

        # V2 Endpoint
        args_schema.endpoint_dest_address = AAZStrArg(
            options=["--endpoint-dest-address"],
            help="Address of the destination of connection monitor endpoint (IP or domain name)",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_dest_coverage_level = AAZStrArg(
            options=["--endpoint-dest-coverage-level"],
            help="Test coverage for the endpoint.",
            enum={"AboveAverage": "AboveAverage", "Average": "Average", "BelowAverage": "BelowAverage",
                  "Default": "Default", "Full": "Full", "Low": "Low"},
            arg_group="V2 Endpoint"
        )
        args_schema.endpoint_dest_name = AAZStrArg(
            options=["--endpoint-dest-name"],
            help="The name of the destination of connection monitor endpoint. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            required=True,
            arg_group="V2 Endpoint"
        )
        args_schema.endpoint_dest_resource_id = AAZStrArg(
            options=["--endpoint-dest-resource-id"],
            help="Resource ID of the destination of connection monitor endpoint.",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_dest_type = AAZStrArg(
            options=["--endpoint-dest-type"],
            help="The endpoint type.",
            enum={"AzureArcVM": "AzureArcVM", "AzureSubnet": "AzureSubnet", "AzureVM": "AzureVM",
                  "AzureVMSS": "AzureVMSS", "AzureVNet": "AzureVNet", "ExternalAddress": "ExternalAddress",
                  "MMAWorkspaceMachine": "MMAWorkspaceMachine", "MMAWorkspaceNetwork": "MMAWorkspaceNetwork"},
            arg_group="V2 Endpoint"
        )
        args_schema.endpoint_source_address = AAZStrArg(
            options=["--endpoint-source-address"],
            help="Address of the source of connection monitor endpoint (IP or domain name).",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_source_coverage_level = AAZStrArg(
            options=["--endpoint-source-coverage-level"],
            help="Test coverage for the endpoint.",
            enum={"AboveAverage": "AboveAverage", "Average": "Average", "BelowAverage": "BelowAverage",
                  "Default": "Default", "Full": "Full", "Low": "Low"},
            arg_group="V2 Endpoint"
        )
        args_schema.endpoint_source_name = AAZStrArg(
            options=["--endpoint-source-name"],
            help="The name of the source of connection monitor endpoint. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            required=True,
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_source_resource_id = AAZStrArg(
            options=["--endpoint-source-resource-id"],
            help="Resource ID of the source of connection monitor endpoint. "
                 "If endpoint is intended to used as source, this option is required.",
            required=True,
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_source_type = AAZStrArg(
            options=["--endpoint-source-type"],
            help="The endpoint type.",
            enum={"AzureArcVM": "AzureArcVM", "AzureSubnet": "AzureSubnet", "AzureVM": "AzureVM",
                  "AzureVMSS": "AzureVMSS", "AzureVNet": "AzureVNet", "ExternalAddress": "ExternalAddress",
                  "MMAWorkspaceMachine": "MMAWorkspaceMachine", "MMAWorkspaceNetwork": "MMAWorkspaceNetwork"},
            arg_group="V2 Endpoint"
        )

        # V2 Output
        args_schema.output_type = AAZStrArg(
            options=["--type", "--output-type"],
            help="Connection monitor output destination type. Currently, only \"Workspace\" is supported.",
            enum={"Workspace": "Workspace"},
            arg_group="V2 Output"
        )
        args_schema.workspace_ids = AAZListArg(
            options=["--workspace-ids"],
            help="Space-separated list of ids of log analytics workspace.",
            arg_group="V2 Output"
        )
        args_schema.workspace_ids.Element = AAZStrArg()

        # V2 Test Configuration
        args_schema.test_config_name = AAZStrArg(
            options=["--test-config-name"],
            help="The name of the connection monitor test configuration. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            required=True,
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_frequency = AAZIntArg(
            options=["--frequency"],
            help="The frequency of test evaluation, in seconds.",
            arg_group="V2 Test Configuration",
            default=60,
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
        args_schema.test_config_tcp_port_behavior = AAZStrArg(
            options=["--tcp-port-behavior"],
            help='Destination port behavior.',
            arg_group="V2 Test Configuration",
            enum={"ListenIfAvailable": "ListenIfAvailable", "None": "None"},
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

        # V2 Test Group
        args_schema.test_group_disable = AAZBoolArg(
            options=["--test-group-disable"],
            help='Value indicating whether test group is disabled. false is default.',
            arg_group="V2 Test Group",
        )
        args_schema.test_group_name = AAZStrArg(
            options=["--test-group-name"],
            help='The name of the connection monitor test group.',
            arg_group="V2 Test Group",
            default="DefaultTestGroup"
        )
        return args_schema

    def pre_operations(self):
        process_nw_cm_v2_create_namespace(self)
        get_network_watcher_from_location(self, watcher_name='network_watcher_name', rg_name='resource_group')
        args = self.ctx.args

        # deal with endpoint
        src_endpoint = {
            "name": args.endpoint_source_name,
            "resource_id": args.endpoint_source_resource_id,
            "address": args.endpoint_source_address,
            "type": args.endpoint_source_type,
            "coverage_level": args.endpoint_source_coverage_level
        }
        dst_endpoint = {
            "name": args.endpoint_dest_name,
            "resource_id": args.endpoint_dest_resource_id,
            "address": args.endpoint_dest_address,
            "type": args.endpoint_dest_type,
            "coverage_level": args.endpoint_dest_coverage_level
        }

        # deal with test configuration
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
                "destination_port_behavior": args.test_config_tcp_port_behavior,
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
            raise ValidationError('Unsupported protocol: "{}" for test configuration'.format(args.test_config_protocol))

        # deal with test group
        test_group = {
            "name": args.test_group_name,
            "disable": args.test_group_disable,
            "test-configurations": [tc['name'] for tc in [test_config]],
            "sources": [e['name'] for e in [src_endpoint]],
            "destinations": [e['name'] for e in [dst_endpoint]]
        }

        # If 'workspace_ids' option is specified but 'output_type' is not
        # then still it should be implicit that 'output-type' is 'Workspace'
        # since only supported value for output_type is 'Workspace' currently.
        if has_value(args.workspace_ids) and not has_value(args.output_type):
            args.output_type = 'Workspace'

        if has_value(args.output_type) and has_value(args.workspace_ids):
            if args.output_type != "Workspace":
                raise ValidationError('Unsupported output type: "{}"'.format(args.output_type))
            args.outputs = []
            for workspace_id in args.workspace_ids:
                output = {
                    "type": args.output_type,
                    "workspace_id": workspace_id,
                }
                args.outputs.append(output)
        else:
            args.outputs = []
        args.endpoints = [src_endpoint, dst_endpoint]
        args.test_configurations = [test_config]
        args.test_groups = [test_group]
