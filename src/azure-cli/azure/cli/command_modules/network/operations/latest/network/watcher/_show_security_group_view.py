# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import AAZResourceLocationArg, AAZStrArg, AAZResourceIdArgFormat
from azure.cli.command_modules.network.aaz.latest.network.watcher._show_security_group_view import ShowSecurityGroupView as _ShowSecurityGroupView
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_vm


class ShowSecurityGroupView(_ShowSecurityGroupView):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of the resource group the target VM is in.",
        )
        args_schema.vm._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute"
                     "/virtualMachines/{}",
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_vm(self)
