# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.monitor.operations.monitor_clone_util import _clone_monitor_metrics_alerts

TYPE_FUNCTION_MAPPTING = {
    'metricsAlert': _clone_monitor_metrics_alerts
}


def clone_existed_settings(cmd, source_resource, target_resource, always_clone=False, monitor_types=['metricsAlert']):
    result = {}
    for monitor_type in monitor_types:
        result[monitor_type] = TYPE_FUNCTION_MAPPTING[monitor_type](cmd, source_resource, target_resource, always_clone)
    return result
