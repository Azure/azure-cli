# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.aaz import has_value
from ..aaz.latest.snapshot import Update as _SnapshotUpdate

logger = get_logger(__name__)


class SnapshotUpdate(_SnapshotUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.disk_access_id._registered = False
        args_schema.disk_encryption_set_id._registered = False

        args_schema.disk_access = AAZStrArg(
            options=["--disk-access"],
            help="Name or ID of the disk access resource for using private endpoints on disks.",
        )
        args_schema.disk_encryption_set = AAZStrArg(
            options=["--disk-encryption-set"],
            help="Name or ID of disk encryption set that is used to encrypt the disk."
        )

        return args_schema

    def pre_instance_update(self, instance):
        from azure.mgmt.core.tools import resource_id, is_valid_resource_id
        from azure.cli.core.commands.client_factory import get_subscription_id

        args = self.ctx.args
        if has_value(args.disk_encryption_set):
            if instance.properties.encryption.type != 'EncryptionAtRestWithCustomerKey' and \
                    has_value(args.encryption_type) and \
                    args.encryption_type != 'EncryptionAtRestWithCustomerKey':
                raise ArgumentUsageError('usage error: Please set --encryption-type to EncryptionAtRestWithCustomerKey')

            disk_encryption_set = args.disk_encryption_set
            if not is_valid_resource_id(disk_encryption_set.to_serialized_data()):
                disk_encryption_set = resource_id(
                    subscription=get_subscription_id(self.cli_ctx), resource_group=args.resource_group,
                    namespace='Microsoft.Compute', type='diskEncryptionSets', name=disk_encryption_set)
            instance.properties.encryption.disk_encryption_set_id = disk_encryption_set

        if has_value(args.disk_access):
            disk_access = args.disk_access
            if not is_valid_resource_id(disk_access.to_serialized_data()):
                disk_access = resource_id(
                    subscription=get_subscription_id(self.cli_ctx), resource_group=args.resource_group,
                    namespace='Microsoft.Compute', type='diskAccesses', name=disk_access)
            instance.properties.disk_access_id = disk_access
