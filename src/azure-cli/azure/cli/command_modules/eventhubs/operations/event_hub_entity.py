# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals
from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.eventhub import Update as _EventHubEntityUpdate


def cli_eventhub_create(cmd, resource_group_name, namespace_name, event_hub_name,
                        partition_count=None, status=None, retention_time_in_hours=None, cleanup_policy=None, tombstone_retention_time_in_hours=None,
                        enable_capture=None, skip_empty_archives=None, capture_interval=None, capture_size_limit=None, destination_name=None,
                        blob_container=None, archive_name_format=None, storage_account=None):

    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.eventhub import Create
    command_arg_dict = {}

    if cleanup_policy:
        command_arg_dict.update({
            "cleanup_policy": cleanup_policy
        })
    if retention_time_in_hours:
        command_arg_dict.update({
            "retention_time_in_hours": int(retention_time_in_hours),
        })
    if tombstone_retention_time_in_hours:
        command_arg_dict.update({
            "tombstone_retention_time_in_hours": tombstone_retention_time_in_hours
        })
    if partition_count:
        command_arg_dict.update({
            "partition_count": int(partition_count)
        })
    if status:
        command_arg_dict.update({
            "status": status
        })
    if enable_capture:
        command_arg_dict.update({
            "archive_name_format": archive_name_format,
            "blob_container": blob_container,
            "capture_interval": int(capture_interval),
            "capture_size_limit": int(capture_size_limit),
            "destination_name": destination_name,
            "enable_capture": bool(enable_capture),
            "encoding": 'Avro',
            "storage_account": storage_account,
            "skip_empty_archives": skip_empty_archives
        })
    command_arg_dict.update({
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "event_hub_name": event_hub_name
    })
    return Create(cli_ctx=cmd.cli_ctx)(command_args=command_arg_dict)


class EventHubEntityUpdate(_EventHubEntityUpdate):
    def pre_operations(self):
        args = self.ctx.args
        from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.eventhub._show import Show

        eventhub = Show(cli_ctx=self.cli_ctx)(command_args={"resource_group": args.resource_group, "namespace_name": args.namespace_name, "event_hub_name": args.event_hub_name})

        if bool(args.enable_capture) is True and not args.encoding and 'captureDescription' not in eventhub:
            args.encoding = 'Avro'
