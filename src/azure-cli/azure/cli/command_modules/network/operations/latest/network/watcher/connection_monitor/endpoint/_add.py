# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.aaz import has_value, AAZResourceLocationArg, AAZListArg, AAZStrArg
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.command_modules.network.aaz.latest.network.watcher.connection_monitor.endpoint._add import Add as _WatcherConnectionMonitorEndpointAdd
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_location


class WatcherConnectionMonitorEndpointAdd(_WatcherConnectionMonitorEndpointAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.filter_items._registered = False
        args_schema.filter_type._registered = False
        args_schema.scope_exclude._registered = False
        args_schema.scope_include._registered = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True
        )
        args_schema.address_exclude = AAZListArg(
            options=["--address-exclude"],
            help="List of address of the endpoint item which needs to be excluded to the endpoint scope.",
        )
        args_schema.address_exclude.Element = AAZStrArg()

        args_schema.address_include = AAZListArg(
            options=["--address-include"],
            help="List of address of the endpoint item which needs to be included to the endpoint scope.",
        )
        args_schema.address_include.Element = AAZStrArg()

        args_schema.dest_test_groups = AAZListArg(
            options=["--dest-test-groups"],
            help="Space-separated list of names for test group to reference as destination.",
            arg_group="V2 Test Group"
        )
        args_schema.dest_test_groups.Element = AAZStrArg()

        args_schema.source_test_groups = AAZListArg(
            options=["--source-test-groups"],
            help="Space-separated list of names for test group to reference as source.",
            arg_group="V2 Test Group"
        )
        args_schema.source_test_groups.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.dest_test_groups) or has_value(args.source_test_groups):
            dest_test_groups, source_test_groups = args.dest_test_groups, args.source_test_groups
            if dest_test_groups is None and source_test_groups is None:
                raise ValidationError('usage error: endpoint has to be referenced from at least one existing '
                                      'test group via --dest-test-groups/--source-test-groups')
        get_network_watcher_from_location(self)

        args.scope_include = assign_aaz_list_arg(
            args.scope_include,
            args.address_include,
            element_transformer=lambda _, tmp_ip: {"address": tmp_ip}
        )

        args.scope_exclude = assign_aaz_list_arg(
            args.scope_exclude,
            args.address_exclude,
            element_transformer=lambda _, tmp_ip: {"address": tmp_ip}
        )

    def pre_instance_create(self):
        args = self.ctx.args
        name = args.endpoint_name.to_serialized_data()
        instance = self.ctx.vars.instance
        src_test_groups = set()
        dst_test_groups = set()
        if has_value(args.source_test_groups):
            src_test_groups = set(args.source_test_groups.to_serialized_data())
        if has_value(args.dest_test_groups):
            dst_test_groups = set(args.dest_test_groups.to_serialized_data())
        for test_group in instance.properties.test_groups:
            if test_group.name.to_serialized_data() in src_test_groups:
                test_group.sources.append(name)
            if test_group.name.to_serialized_data() in dst_test_groups:
                test_group.destinations.append(name)
