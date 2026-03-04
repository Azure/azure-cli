# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import AAZResourceLocationArg, AAZResourceLocationArgFormat
from azure.cli.command_modules.network.aaz.latest.network.watcher.flow_log._list import List as _NwFlowLogList
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_location


class NwFlowLogList(_NwFlowLogList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group._registered = False
        args_schema.resource_group._required = False
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location to identify the exclusive Network Watcher under a region. "
                 "Only one Network Watcher can be existed per subscription and region.",
            required=True,
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group",
            ),
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group')
