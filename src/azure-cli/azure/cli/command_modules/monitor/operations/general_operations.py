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


def clone_existed_settings(cmd, source_resource, target_resource, always_clone=False, monitor_types=None):
    result = {}
    monitor_types = set(monitor_types)
    if "metricsAlert" in monitor_types:
        result["metricsAlert"] = _clone_monitor_metrics_alerts(cmd, source_resource, target_resource, always_clone)
    return result

