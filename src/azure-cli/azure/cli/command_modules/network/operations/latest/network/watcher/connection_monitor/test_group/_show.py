# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import AAZResourceLocationArg
from azure.cli.command_modules.network.aaz.latest.network.watcher.connection_monitor.test_group._show import Show as _WatcherConnectionMonitorTestGroupShow
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_location


class WatcherConnectionMonitorTestGroupShow(_WatcherConnectionMonitorTestGroupShow):

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
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)
