# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import AzureResponseError, ForbiddenError, InvalidArgumentValueError
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from knack.log import get_logger

logger = get_logger(__name__)

TRACE_CONTAINER_DEFAULTS = {
    "retention_days": 30,
    "trace_duration_window": 600,
    "trace_metrics": "Enabled",
}
_TRACE_CONTAINER_PROPERTIES = {
    "retention_days": "traceRetentionInDays",
    "trace_duration_window": "traceDurationWindowInSeconds",
    "trace_metrics": "traceMetricsState",
}


def parse_workspace_id(workspace_id):
    """Return the trace container command arguments for an Azure Monitor workspace resource ID."""
    from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
    parts = parse_resource_id(workspace_id) if is_valid_resource_id(workspace_id or "") else {}
    is_workspace = (parts.get("namespace", "").lower() == "microsoft.monitor" and
                    parts.get("type", "").lower() == "accounts" and not parts.get("child_name_1"))
    if not is_workspace:
        raise InvalidArgumentValueError(
            "--azure-monitor-workspace must be the resource ID of an Azure Monitor workspace "
            "(Microsoft.Monitor/accounts).")
    return {
        "subscription": parts["subscription"],
        "resource_group": parts["resource_group"],
        "azure_monitor_workspace_name": parts["name"],
    }


def get_trace_container(cli_ctx, workspace):
    """Return the trace container of a workspace, or None if it has none."""
    from azure.cli.command_modules.monitor.aaz.latest.monitor.account.trace_container._show import Show
    try:
        return Show(cli_ctx=cli_ctx)(command_args=workspace)
    except ResourceNotFoundError:
        return None


def trace_container_settings(container):
    """Return the settings of a trace container, keyed by argument name."""
    properties = container.get("properties") or {}
    settings = {}
    for name, property_name in _TRACE_CONTAINER_PROPERTIES.items():
        value = properties.get(property_name)
        # Containers created before a setting existed use the service default for it.
        settings[name] = TRACE_CONTAINER_DEFAULTS[name] if value is None else value
    return settings


def _container_create_command(workspace):
    return "az monitor account trace-container create --subscription {} -g {} -w {}".format(
        workspace["subscription"], workspace["resource_group"], workspace["azure_monitor_workspace_name"])


def _wait_for_container(cli_ctx, workspace):
    from azure.cli.command_modules.monitor.aaz.latest.monitor.account.trace_container._show import Show
    from azure.cli.core.commands.command_operation import WaitCommandOperation

    def get_container(**command_args):
        return Show(cli_ctx=cli_ctx)(command_args=command_args)

    timeout_error = WaitCommandOperation.wait(
        command_args={**workspace, "created": True, "updated": False, "deleted": False, "exists": False,
                      "custom": None, "interval": 5, "timeout": 1800},
        cli_ctx=cli_ctx,
        getter=get_container)
    if timeout_error:
        raise timeout_error
    return get_trace_container(cli_ctx, workspace)


def ensure_trace_container(cli_ctx, workspace_id, retention_days=None, trace_metrics=None):
    """Create the trace container of a workspace if it has none, or check that the existing one is usable.

    An existing container is never changed. Explicit settings that differ from it are rejected.
    """
    workspace = parse_workspace_id(workspace_id)
    try:
        container = get_trace_container(cli_ctx, workspace)
    except HttpResponseError as ex:
        if ex.status_code == 403:
            raise ForbiddenError(
                "Reading the trace container of {} was denied. You need read access to that Azure Monitor "
                "workspace.".format(workspace_id)) from ex
        raise

    if container is None:
        settings = dict(TRACE_CONTAINER_DEFAULTS)
        if retention_days is not None:
            settings["retention_days"] = retention_days
        if trace_metrics is not None:
            settings["trace_metrics"] = trace_metrics
        from azure.cli.command_modules.monitor.aaz.latest.monitor.account.trace_container._create import Create
        from azure.cli.core.commands import LongRunningOperation
        try:
            container = LongRunningOperation(cli_ctx)(
                Create(cli_ctx=cli_ctx)(command_args={**workspace, **settings}))
        except HttpResponseError as ex:
            if ex.status_code == 403:
                raise ForbiddenError(
                    "Creating the trace container of {} was denied. Ask the owner of that Azure Monitor workspace "
                    "to run:\n  {}\nThen run this command again.".format(
                        workspace_id, _container_create_command(workspace))) from ex
            raise
        logger.warning("Created the trace container of %s: retention %s days, trace metrics %s.",
                       workspace_id, settings["retention_days"], settings["trace_metrics"])
        return container

    state = (container.get("properties") or {}).get("provisioningState")
    if state in ("Failed", "Canceled"):
        raise AzureResponseError(
            "The trace container of {} is in the {} state. Retry it with "
            "'az monitor account trace-container update --subscription {} -g {} -w {}', then run this command "
            "again.".format(workspace_id, state, workspace["subscription"], workspace["resource_group"],
                            workspace["azure_monitor_workspace_name"]))
    if state not in (None, "Succeeded"):
        container = _wait_for_container(cli_ctx, workspace)

    settings = trace_container_settings(container)
    for name, option, value in (("retention_days", "--trace-retention-days", retention_days),
                                ("trace_metrics", "--trace-metrics", trace_metrics)):
        if value is not None and value != settings[name]:
            raise InvalidArgumentValueError(
                "The trace container of {workspace} already exists with {option} {value}. This command does not "
                "change an existing container. Omit {option}, or change the container with "
                "'az monitor account trace-container update'.".format(
                    workspace=workspace_id, option=option, value=settings[name]))
    logger.warning("Using the existing trace container of %s: retention %s days, trace metrics %s.",
                   workspace_id, settings["retention_days"], settings["trace_metrics"])
    return container
