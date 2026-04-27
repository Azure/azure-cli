# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Context-enriched error builder for az webapp deploy / az webapp up.
Enabled via the --enriched-errors flag on az webapp deploy / az webapp up.
"""

import re

from knack.log import get_logger
from knack.util import CLIError

from ._deployment_failure_patterns import match_failure_pattern

logger = get_logger(__name__)


class EnrichedDeploymentError(CLIError):
    # A CLIError subclass for context-enriched deployment failures.
    pass


_STATUS_CODE_PATTERNS = [
    re.compile(r'Status\s*Code[:\s]+(\d{3})', re.IGNORECASE),   # "Status Code: 400"
    re.compile(r'\(([45]\d{2})\)'),                             # "Bad Request(400)"
    re.compile(r'HTTP\s+(\d{3})', re.IGNORECASE),                # "HTTP 504"
    re.compile(
        r'\b([45]\d{2})\s+(?:Bad|Unauthorized|Forbidden|Not\s+Found|Conflict'
        r'|Too\s+Many|Internal|Gateway|Service)', re.IGNORECASE),  # "400 Bad Request"
]


def extract_status_code_from_message(message):
    if not message:
        return None
    for pattern in _STATUS_CODE_PATTERNS:
        m = pattern.search(message)
        if m:
            code = int(m.group(1))
            if 400 <= code <= 599:
                return code
    return None


def _get_app_runtime(cmd, resource_group_name, webapp_name, slot=None):
    try:
        from ._client_factory import web_client_factory
        client = web_client_factory(cmd.cli_ctx)
        if slot:
            config = client.web_apps.get_configuration_slot(resource_group_name, webapp_name, slot)
        else:
            config = client.web_apps.get_configuration(resource_group_name, webapp_name)
        if config.linux_fx_version:
            return config.linux_fx_version
        return "Unknown"
    except Exception:  # pylint: disable=broad-except
        return "Unknown"


def _get_app_region_and_plan_sku(cmd, resource_group_name, webapp_name):
    try:
        from ._client_factory import web_client_factory
        from azure.mgmt.core.tools import parse_resource_id
        client = web_client_factory(cmd.cli_ctx)
        app = client.web_apps.get(resource_group_name, webapp_name)
        region = app.location if app else "Unknown"
        sku = "Unknown"
        if app and app.server_farm_id:
            plan_parts = parse_resource_id(app.server_farm_id)
            plan = client.app_service_plans.get(plan_parts['resource_group'], plan_parts['name'])
            if plan and plan.sku:
                sku = plan.sku.name
        return region, sku
    except Exception:  # pylint: disable=broad-except
        return "Unknown", "Unknown"


_ARTIFACT_TYPE_MAP = {
    'zip': 'ZipDeploy', 'war': 'WarDeploy', 'jar': 'JarDeploy',
    'ear': 'EarDeploy', 'startup': 'StartupFile', 'static': 'StaticDeploy'
}


def _determine_deployment_type(params=None, *, src_url=None, artifact_type=None):
    _src_url = src_url if src_url is not None else (getattr(params, 'src_url', None) if params else None)
    _artifact = artifact_type if artifact_type is not None else (
        getattr(params, 'artifact_type', None) if params else None)

    if _src_url:
        return "OneDeploy (URL-based)"

    return _ARTIFACT_TYPE_MAP.get(_artifact, "OneDeploy")


def build_enriched_error_context(params=None, *, cmd=None, resource_group_name=None,  # pylint: disable=too-many-locals
                                 webapp_name=None, slot=None, src_url=None,
                                 artifact_type=None, status_code=None, error_message=None,
                                 deployment_status=None,
                                 last_known_step=None, kudu_status=None):
    _cmd = cmd or (params.cmd if params else None)
    _rg = resource_group_name or (params.resource_group_name if params else None)
    _name = webapp_name or (params.webapp_name if params else None)
    _slot = slot if slot is not None else (
        getattr(params, 'slot', None) if params else None)
    _src_url = src_url if src_url is not None else (
        getattr(params, 'src_url', None) if params else None)
    _artifact = artifact_type if artifact_type is not None else (
        getattr(params, 'artifact_type', None) if params else None)

    pattern = match_failure_pattern(
        status_code=status_code,
        error_message=error_message,
    )

    # Build base context
    context = {}

    if pattern:
        context["errorCode"] = pattern["errorCode"]
        context["stage"] = pattern["stage"]
    else:
        context["errorCode"] = f"HTTP_{status_code}" if status_code else "UnknownDeploymentError"
        context["stage"] = deployment_status or "Unknown"

    # App metadata (best-effort)
    if _cmd and _rg and _name:
        context["runtime"] = _get_app_runtime(_cmd, _rg, _name, _slot)
        region, plan_sku = _get_app_region_and_plan_sku(_cmd, _rg, _name)
        context["region"] = region
        context["planSku"] = plan_sku
    else:
        context["runtime"] = "Unknown"
        context["region"] = "Unknown"
        context["planSku"] = "Unknown"

    context["deploymentType"] = _determine_deployment_type(
        params, src_url=_src_url, artifact_type=_artifact
    )

    # Suggested fixes
    if pattern:
        context["suggestedFixes"] = pattern["suggestedFixes"]
    else:
        context["suggestedFixes"] = [
            "Check deployment logs: 'az webapp log deployment show -n {} -g {}'".format(
                _name or '<app>', _rg or '<rg>'),
            "Check runtime logs: 'az webapp log tail -n {} -g {}'".format(
                _name or '<app>', _rg or '<rg>')
        ]

    # Extra diagnostics
    if last_known_step:
        context["lastKnownStep"] = last_known_step
    if kudu_status:
        context["kuduStatus"] = str(kudu_status)

    # Raw details
    if error_message:
        if len(error_message) > 500:
            context["rawError"] = error_message[:500] + "... [truncated]"
        else:
            context["rawError"] = error_message

    return context


def format_enriched_error_message(context):
    lines = []
    lines.append("")
    lines.append("=" * 72)
    lines.append("DEPLOYMENT FAILED: Context-Enriched Diagnostics")
    lines.append("=" * 72)
    lines.append("")

    lines.append(f"Error Code  : {context.get('errorCode', 'Unknown')}")
    lines.append(f"Stage       : {context.get('stage', 'Unknown')}")
    lines.append(f"Runtime     : {context.get('runtime', 'Unknown')}")
    lines.append(f"Deploy Type : {context.get('deploymentType', 'Unknown')}")
    lines.append(f"Region      : {context.get('region', 'Unknown')}")
    lines.append(f"Plan SKU    : {context.get('planSku', 'Unknown')}")
    if context.get("lastKnownStep"):
        lines.append(f"Last Step   : {context['lastKnownStep']}")
    if context.get("kuduStatus"):
        lines.append(f"Kudu Status : {context['kuduStatus']}")
    lines.append("")

    if context.get("rawError"):
        lines.append(f"Raw Error   : {context['rawError']}")
        lines.append("")

    fixes = context.get("suggestedFixes", [])
    if fixes:
        lines.append("Suggested Fixes:")
        for f in fixes:
            lines.append(f"  - {f}")
        lines.append("")

    # Copilot prompt
    lines.append("-" * 72)
    lines.append("  Copy the full error output above and paste it into GitHub Copilot Chat")
    lines.append("  with the prompt: 'Why did my Linux App Service deployment fail and how do I fix it?'")
    lines.append("-" * 72)

    return "\n".join(lines)


def raise_enriched_deployment_error(params=None, *, cmd=None, resource_group_name=None,
                                    webapp_name=None, slot=None, src_url=None,
                                    artifact_type=None, status_code=None, error_message=None,
                                    deployment_status=None,
                                    last_known_step=None, kudu_status=None):
    context = build_enriched_error_context(
        params=params,
        cmd=cmd,
        resource_group_name=resource_group_name,
        webapp_name=webapp_name,
        slot=slot,
        src_url=src_url,
        artifact_type=artifact_type,
        status_code=status_code,
        error_message=error_message,
        deployment_status=deployment_status,
        last_known_step=last_known_step,
        kudu_status=kudu_status
    )

    logger.debug("Deployment failure context: %s", context)

    message = format_enriched_error_message(context)
    raise EnrichedDeploymentError(message)
