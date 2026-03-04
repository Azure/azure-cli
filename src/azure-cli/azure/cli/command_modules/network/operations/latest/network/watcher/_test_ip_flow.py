# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.aaz import AAZResourceLocationArg, AAZStrArg, AAZResourceIdArgFormat
from azure.cli.command_modules.network.aaz.latest.network.watcher._test_ip_flow import TestIpFlow as _TestIPFlow
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_vm


class TestIPFlow(_TestIPFlow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        args_schema.local = AAZStrArg(
            options=["--local"],
            help="Private IPv4 address for the VMs NIC and the port of the packet in X.X.X.X:PORT format. "
                 "`*` can be used for port when direction is outbound.",
            required=True,
        )
        args_schema.remote = AAZStrArg(
            options=["--remote"],
            help="IPv4 address and port for the remote side of the packet X.X.X.X:PORT format. "
                 "`*` can be used for port when the direction is inbound.",
            required=True,
        )
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of the resource group the target VM is in.",
        )
        args_schema.vm._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute"
                     "/virtualMachines/{}",
        )
        args_schema.nic._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Network"
                     "/networkInterfaces/{}",
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        args_schema.local_ip_address._required = False
        args_schema.local_ip_address._registered = False
        args_schema.local_port._required = False
        args_schema.local_port._registered = False
        args_schema.remote_ip_address._required = False
        args_schema.remote_ip_address._registered = False
        args_schema.remote_port._required = False
        args_schema.remote_port._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        try:
            args.local_ip_address, args.local_port = args.local.to_serialized_data().split(":")
            args.remote_ip_address, args.remote_port = args.remote.to_serialized_data().split(":")
        except:
            raise ValidationError("usage error: the format of the '--local' and '--remote' should be like x.x.x.x:port")

        get_network_watcher_from_vm(self)
