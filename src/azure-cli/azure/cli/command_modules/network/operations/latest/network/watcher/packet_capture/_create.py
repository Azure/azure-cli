# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.aaz import has_value, AAZResourceLocationArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
from azure.cli.command_modules.network.aaz.latest.network.watcher.packet_capture._create import Create as _PacketCaptureCreate
from azure.cli.command_modules.network.operations.latest.network.watcher._helpers import get_network_watcher_from_vm, get_network_watcher_from_vmss


class PacketCaptureCreate(_PacketCaptureCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of the resource group the target resource is in.",
            required=True,
        )
        args_schema.vm = AAZResourceIdArg(
            options=["--vm"],
            help="Name or ID of the VM to target",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute"
                         "/virtualMachines/{}",
            ),
        )
        args_schema.target._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute"
                     "/virtualMachineScaleSets/{}",
        )
        args_schema.storage_account._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Storage"
                     "/storageAccounts/{}",
        )
        args_schema.target._required = False
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.target_type) and args.target_type.to_serialized_data().lower() == "azurevmss":
            get_network_watcher_from_vmss(self)
        else:
            # set the appropriate fields if target is vm
            get_network_watcher_from_vm(self)
            args.target = args.vm
            args.include, args.exclude = None, None

        storage_usage = ValidationError("usage error: --storage-account NAME_OR_ID [--storage-path PATH] [--file-path PATH] | --file-path PATH")
        if not has_value(args.storage_account) and (has_value(args.storage_path) or not has_value(args.file_path)):
            raise storage_usage

        if has_value(args.file_path):
            path = args.file_path.to_serialized_data()
            if not path.endswith(".cap"):
                raise ValidationError("usage error: --file-path PATH must end with the '*.cap' extension")

            if not path.startswith("/"):
                path = path.replace("/", "\\")
            args.file_path = path
