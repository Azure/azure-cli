# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.util import user_confirmation
from azure.core.exceptions import HttpResponseError
from knack.log import get_logger

logger = get_logger(__name__)

_AAZ_PACKAGE = "azure.cli.command_modules.monitor.aaz.latest.monitor.trace_association"
_SCOPE_PATTERN = re.compile(
    r"/subscriptions/(?P<subscription>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    r"(?:/resourceGroups/(?P<resource_group>[^/]+)"
    r"(?:/providers/Microsoft\.Insights/components/(?P<component>[^/]+))?)?",
    re.IGNORECASE)
_ASSOCIATION_SUFFIX = re.compile(r"/providers/Microsoft\.Monitor/traceAssociations/default$", re.IGNORECASE)


class _Scope:  # pylint: disable=too-few-public-methods
    """A trace association scope: an Application Insights component, a resource group or a subscription."""

    def __init__(self, resource_uri):
        match = _SCOPE_PATTERN.fullmatch((resource_uri or "").rstrip("/"))
        if match is None:
            raise InvalidArgumentValueError(
                "--resource-uri must be the resource ID of an Application Insights component, a resource group "
                "or a subscription.")
        subscription, resource_group, component = match.group("subscription", "resource_group", "component")
        self.id = "/subscriptions/" + subscription
        self.args = {"subscription": subscription}
        self.kind = "subscription"
        if resource_group:
            self.id += "/resourceGroups/" + resource_group
            self.args["resource_group"] = resource_group
            self.kind = "resource_group"
        if component:
            self.id += "/providers/Microsoft.Insights/components/" + component
            self.args.update(provider_name="Microsoft.Insights", provider_type="components", resource_name=component)
            self.kind = "resource"

    def aaz_command(self, name):
        """Return the generated trace association command of this scope's kind, e.g. 'show'."""
        from importlib import import_module
        module = import_module("{}.{}._{}".format(_AAZ_PACKAGE, self.kind, name))
        return getattr(module, name.capitalize())


def _association_scope(association):
    return _ASSOCIATION_SUFFIX.sub("", association.get("id") or "")


def _workspace_of(association):
    return (association.get("properties") or {}).get("azureMonitorWorkspaceResourceId")


def _same_id(first, second):
    return (first or "").rstrip("/").lower() == (second or "").rstrip("/").lower()


def _list(cli_ctx, scope):
    return list(scope.aaz_command("list")(cli_ctx=cli_ctx)(command_args=scope.args))


def _report_destinations(scope, associations):
    destinations = {}
    for association in associations:
        workspace = _workspace_of(association)
        if workspace:
            destinations.setdefault(workspace.lower(), (workspace, []))[1].append(_association_scope(association))
    if not destinations:
        logger.warning("No trace associations apply to %s.", scope.id)
        return
    logger.warning("Traces from %s go to:", scope.id)
    for workspace, scopes in destinations.values():
        logger.warning("  %s, through %s", workspace, ", ".join(scopes))


def create_trace_association(cmd, resource_uri, azure_monitor_workspace, trace_retention_days=None,
                             trace_metrics=None, yes=False):
    from azure.cli.command_modules.monitor.operations.trace_container import (
        ensure_trace_container, parse_workspace_id, workspace_write_access_error)
    scope = _Scope(resource_uri)
    parse_workspace_id(azure_monitor_workspace)
    if trace_retention_days is not None and not 4 <= trace_retention_days <= 730:
        raise InvalidArgumentValueError("--trace-retention-days must be between 4 and 730.")

    own = next((a for a in _list(cmd.cli_ctx, scope) if _same_id(_association_scope(a), scope.id)), None)
    replaced = _workspace_of(own) if own and not _same_id(_workspace_of(own), azure_monitor_workspace) else None
    if scope.kind != "resource":
        if replaced:
            user_confirmation(
                "{scope} sends traces to {old}. Replace it with {new}? Resources under it stop sending traces to "
                "{old} unless another association routes them there.".format(
                    scope=scope.id, old=replaced, new=azure_monitor_workspace),
                yes)
        logger.warning("Only Application Insights components in regions with traces enabled send traces. "
                       "Associations at a resource group or subscription are not checked for region.")

    ensure_trace_container(cmd.cli_ctx, azure_monitor_workspace, trace_retention_days, trace_metrics)
    try:
        association = scope.aaz_command("create")(cli_ctx=cmd.cli_ctx)(command_args={
            **scope.args, "azure_monitor_workspace": azure_monitor_workspace})
    except HttpResponseError as ex:
        logger.warning("The trace container is ready, but the association at %s was not written. Run this command "
                       "again after fixing the error below.", scope.id)
        # ARM checks that the caller can write the workspace the association points to.
        if ex.status_code == 403 and ex.error and ex.error.code == "LinkedAuthorizationFailed":
            raise workspace_write_access_error("Sending traces from {} to {} was denied.".format(
                scope.id, azure_monitor_workspace)) from ex
        raise
    if replaced:
        logger.warning("Replaced %s with %s at %s.", replaced, azure_monitor_workspace, scope.id)

    try:
        associations = _list(cmd.cli_ctx, scope)
    except HttpResponseError:
        logger.warning("The association at %s now points to %s, but listing the associations that apply failed. "
                       "Running this command again is safe.", scope.id, azure_monitor_workspace)
        raise
    _report_destinations(scope, associations)
    return association


def show_trace_association(cmd, resource_uri):
    scope = _Scope(resource_uri)
    return scope.aaz_command("show")(cli_ctx=cmd.cli_ctx)(command_args=scope.args)


def list_trace_associations(cmd, resource_uri):
    return _list(cmd.cli_ctx, _Scope(resource_uri))


def delete_trace_association(cmd, resource_uri, yes=False):
    scope = _Scope(resource_uri)
    associations = _list(cmd.cli_ctx, scope)
    own = next((a for a in associations if _same_id(_association_scope(a), scope.id)), None)
    if own is None:
        logger.warning("No trace association is configured at %s.", scope.id)
        _report_destinations(scope, associations)
        return
    if scope.kind != "resource":
        user_confirmation(
            "Delete the trace association at {}? Resources under it stop sending traces to {} unless another "
            "association routes them there.".format(scope.id, _workspace_of(own)), yes)

    scope.aaz_command("delete")(cli_ctx=cmd.cli_ctx)(command_args=scope.args)
    logger.warning("Deleted the trace association at %s. The Azure Monitor workspace and its trace container are "
                   "unchanged.", scope.id)
    try:
        associations = _list(cmd.cli_ctx, scope)
    except HttpResponseError:
        logger.warning("The association at %s is deleted, but listing the associations that still apply failed. "
                       "Running this command again is safe.", scope.id)
        raise
    _report_destinations(scope, associations)
