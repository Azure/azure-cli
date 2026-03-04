# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value, AAZResourceLocationArg, AAZListArg, AAZStrArg, AAZDictArg
from azure.cli.command_modules.network.aaz.latest.network.watcher.connection_monitor.test_configuration._add import Add as _MonitorTestConfigurationAdd
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_location


class WatcherConnectionMonitorTestConfigurationAdd(_MonitorTestConfigurationAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False
        args_schema.http_request_headers._registered = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        args_schema.http_request_header = AAZDictArg(
            options=["--http-request-header"],
            help="The HTTP headers to transmit with the request. List of property=value pairs to define HTTP headers.",
            arg_group="HTTP Protocol",
        )
        args_schema.http_request_header.Element = AAZStrArg()

        args_schema.test_groups = AAZListArg(
            options=["--test-groups"],
            help="Space-separated list of names of test group which only need to be affected if specified.",
            required=True,
        )
        args_schema.test_groups.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)

    def pre_instance_create(self):
        args = self.ctx.args
        name = args.test_configuration_name.to_serialized_data()

        if has_value(args.http_request_header):
            for tmp_name, val in args.http_request_header.items():
                args.http_request_headers.append({
                    "name": tmp_name,
                    "value": val,
                })

        instance = self.ctx.vars.instance
        if has_value(args.test_groups):
            for test_group in instance.properties.test_groups:
                if test_group.name.to_serialized_data() in args.test_groups:
                    test_group.test_configurations.append(name)
