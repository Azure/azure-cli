# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value, AAZResourceLocationArg, AAZListArg, AAZStrArg
from azure.cli.command_modules.network.aaz.latest.network.watcher.connection_monitor.endpoint._remove import Remove as _WatcherConnectionMonitorEndpointRemove
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_location


class WatcherConnectionMonitorEndpointRemove(_WatcherConnectionMonitorEndpointRemove):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        args_schema.test_groups = AAZListArg(
            options=["--test-groups"],
            help="Space-separated list of names of test group which only need to "
                 "be affected if specified.",
            arg_group="V2 Test Group",
        )
        args_schema.test_groups.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)

    def post_instance_delete(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        name = args.endpoint_name.to_serialized_data()
        # refresh test groups

        temp_test_groups = instance.properties.test_groups
        if has_value(args.test_groups):
            temp_test_groups = [t for t in instance.properties.test_groups
                                if t.name.to_serialized_data() in args.test_groups]

        for test_group in temp_test_groups:
            test_group.sources = [tc for tc in test_group.sources if tc != name]
            test_group.destinations = [tc for tc in test_group.destinations if tc != name]
