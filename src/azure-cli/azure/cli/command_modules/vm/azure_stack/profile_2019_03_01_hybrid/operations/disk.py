# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from ._util import import_aaz_by_profile

logger = get_logger(__name__)

_Disk = import_aaz_by_profile("disk")


class DiskUpdate(_Disk.Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.disk_encryption_set_id._registered = False
        args_schema.data_access_auth_mode._registered = False
        args_schema.disk_access_id._registered = False
        args_schema.public_network_access._registered = False
        args_schema.accelerated_network._registered = False
        args_schema.architecture._registered = False
        args_schema.encryption_type._registered = False
        args_schema.disk_iops_read_write._registered = False
        args_schema.disk_mbps_read_write._registered = False
        args_schema.network_access_policy._registered = False

        return args_schema


class DiskGrantAccess(_Disk.GrantAccess):
    def pre_operations(self):
        args = self.ctx.args

        disk_info = _Disk.Show(cli_ctx=self.cli_ctx)(command_args={
            "disk_name": args.disk_name,
            "resource_group": args.resource_group
        })

        if disk_info.get("creation_data", None) and \
                disk_info["creation_data"].get("create_option", None) == "UploadPreparedSecure":
            args.secure_vm_guest_state_sas = True
