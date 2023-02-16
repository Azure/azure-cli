# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger
from knack.util import CLIError
from ..aaz.latest.network.watcher import Create as WatcherCreate, Update as WatcherUpdate

from ..aaz.latest.network.watcher.connection_monitor import Start as _WatcherConnectionMonitorStart
from ..aaz.latest.network.watcher.connection_monitor import Stop as _WatcherConnectionMonitorStop
from ..aaz.latest.network.watcher.connection_monitor import Show as _WatcherConnectionMonitorShow
from ..aaz.latest.network.watcher.connection_monitor import List as _WatcherConnectionMonitorList
from ..aaz.latest.network.watcher.connection_monitor import Delete as _WatcherConnectionMonitorDelete
from ..aaz.latest.network.watcher.connection_monitor import Query as _WatcherConnectionMonitorQuery

from azure.cli.core.aaz import AAZStrArg
from azure.cli.core.commands import LongRunningOperation

logger = get_logger(__name__)

def update_network_watcher_from_location(ctx, remove=False, watcher_name='watcher_name',
                                         rg_name='watcher_rg'):

    from ..aaz.latest.network.watcher import List as NetworkWatcherList
    parameters = {
        'subscription_id': ctx.subscription_id
    }
    network_watcher_poller = NetworkWatcherList(cli_ctx=ctx)(command_args=parameters)
    network_watcher_list = LongRunningOperation(ctx)(network_watcher_poller)
    args = ctx.args
    location = args.location.to_serialized_data()
    watcher = next((x for x in list(network_watcher_list) if x.location.lower() == location.lower()), None)
    if not watcher:
        raise CLIError("network watcher is not enabled for region '{}'.".format(location))
    from azure.mgmt.core.tools import parse_resource_id
    id_parts = parse_resource_id(watcher.id)
    setattr(args, rg_name, id_parts['resource_group'])
    setattr(args, watcher_name, id_parts['name'])
    if remove:
        del args.location


class WatcherConnectionMonitorStart(_WatcherConnectionMonitorStart):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.resource_group._registered = False
        args_schema.location = AAZStrArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             remove=True,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


class WatcherConnectionMonitorStop(_WatcherConnectionMonitorStop):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.resource_group._registered = False
        args_schema.location = AAZStrArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             remove=True,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


class WatcherConnectionMonitorList(_WatcherConnectionMonitorList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.resource_group._registered = False
        args_schema.location = AAZStrArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             remove=True,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


class WatcherConnectionMonitorShow(_WatcherConnectionMonitorShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.resource_group._registered = False
        args_schema.location = AAZStrArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             remove=True,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


class WatcherConnectionMonitorQuery(_WatcherConnectionMonitorQuery):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.resource_group._registered = False
        args_schema.location = AAZStrArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             remove=True,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


class WatcherConnectionMonitorDelete(_WatcherConnectionMonitorDelete):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.resource_group._registered = False
        args_schema.location = AAZStrArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             remove=True,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')