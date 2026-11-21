# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.monitor.aaz.latest.monitor.account.trace_container._create \
    import Create as _TraceContainerCreate
from azure.cli.command_modules.monitor.operations.trace_container import (
    TRACE_CONTAINER_DEFAULTS, get_trace_container, trace_container_settings,
)


class TraceContainerCreate(_TraceContainerCreate):
    def pre_operations(self):
        from azure.cli.core.aaz import has_value
        args = self.ctx.args
        container = get_trace_container(self.cli_ctx, {
            "subscription": self.ctx.subscription_id,
            "resource_group": args.resource_group.to_serialized_data(),
            "azure_monitor_workspace_name": args.azure_monitor_workspace_name.to_serialized_data(),
        })
        # The service requires every setting, so omitted ones keep their current or default values.
        settings = TRACE_CONTAINER_DEFAULTS if container is None else trace_container_settings(container)
        for name, value in settings.items():
            if not has_value(getattr(args, name)):
                setattr(args, name, value)
