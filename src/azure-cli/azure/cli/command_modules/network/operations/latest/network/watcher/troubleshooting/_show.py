# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value, AAZResourceLocationArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
from azure.cli.command_modules.network.aaz.latest.network.watcher.troubleshooting._show import Show as _NwTroubleshootingShow
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_resource


class NwTroubleshootingShow(_NwTroubleshootingShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._required = False
        args_schema.target_resource_id._registered = False
        args_schema.target_resource_id._required = False
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of resource group. You can configure the default group using `az configure --defaults group=<name>`.",
        )
        args_schema.resource_type = AAZStrArg(
            options=["-t", "--resource-type"],
            help="The resource type.",
            enum={"vnetGateway": "virtualNetworkGateways", "vpnConnection": "connections"},
        )
        args_schema.resource = AAZResourceIdArg(
            options=["--resource"],
            help="Name or ID of the resource to troubleshoot.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/{resource_type}/{}"
            )
        )
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        get_network_watcher_from_resource(self)
        if has_value(args.resource):
            args.target_resource_id = args.resource
