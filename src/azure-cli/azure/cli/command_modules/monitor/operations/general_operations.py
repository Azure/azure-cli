# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from .._client_factory import cf_monitor
from ..util import _gen_guid
from azure.cli.core.commands.transform import _parse_id
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.tools import parse_resource_id
from azure.cli.command_modules.monitor.operations.monitor_clone_util import _clone_monitor_metrics_alerts


logger = get_logger(__name__)
CLONED_NAME = "cloned-{}-{}"
TYPE_FUNCTION_MAPPTING = {
    'metricsAlert': _clone_monitor_metrics_alerts
}


def clone_existed_settings(cmd, source_resource, target_resource, always_clone=False, monitor_types=['metricsAlert']):
    result = {}
    for monitor_type in monitor_types:
        result[monitor_type] = TYPE_FUNCTION_MAPPTING[monitor_type](cmd, source_resource, target_resource, always_clone)
    return result

