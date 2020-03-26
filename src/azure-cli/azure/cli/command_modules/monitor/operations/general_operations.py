# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.monitor.operations.monitor_clone_util import _clone_monitor_metrics_alerts


def clone_existed_settings(cmd, source_resource, target_resource, always_clone=False, monitor_types=None):
    result = {}
    monitor_types = set(monitor_types)
    if "metricsAlert" in monitor_types:
        result["metricsAlert"] = _clone_monitor_metrics_alerts(cmd, source_resource, target_resource, always_clone)
    return result
