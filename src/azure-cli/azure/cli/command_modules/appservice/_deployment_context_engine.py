# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Context-enriched error builder for az webapp deploy / az functionapp deploy.

Instead of raising a bare "Status Code: 504" error, this module builds a structured
diagnostic context block that includes the error code, deployment stage, runtime info,
common causes, suggested fixes, and a ready-to-use Copilot prompt.
"""

import yaml
from knack.log import get_logger
from knack.util import CLIError

from ._deployment_failure_patterns import match_failure_pattern

logger = get_logger(__name__)


def _safe_yaml_dump(data):
    """Dump dict to YAML string, falling back to repr on error."""
    try:
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True).rstrip()
    except Exception:  # pylint: disable=broad-except
        return repr(data)


def _get_app_runtime(cmd, resource_group_name, webapp_name, slot=None):
    """Fetch the runtime name/version from the webapp config."""
    try:
        from ._client_factory import web_client_factory
        client = web_client_factory(cmd.cli_ctx)
        if slot:
            config = client.web_apps.get_configuration_slot(resource_group_name, webapp_name, slot)
        else:
            config = client.web_apps.get_configuration(resource_group_name, webapp_name)
        # Linux apps store runtime in linux_fx_version (e.g. "PYTHON|3.11")
        if config.linux_fx_version:
            return config.linux_fx_version
        # Windows apps: check e.g. net_framework_version, java_version, python_version, etc.
        for attr in ('net_framework_version', 'java_version', 'python_version',
                     'php_version', 'node_version', 'power_shell_version'):
            val = getattr(config, attr, None)
            if val:
                return f"{attr.replace('_version', '').replace('_', ' ').title()} {val}"
        return "Unknown"
    except Exception:  # pylint: disable=broad-except
        return "Unknown"


def _get_app_region(cmd, resource_group_name, webapp_name):
    """Fetch the Azure region of the web app."""
    try:
        from ._client_factory import web_client_factory
        client = web_client_factory(cmd.cli_ctx)
        app = client.web_apps.get(resource_group_name, webapp_name)
        return app.location if app else "Unknown"
    except Exception:  # pylint: disable=broad-except
        return "Unknown"


def _get_app_plan_sku(cmd, resource_group_name, webapp_name):
    """Fetch the App Service plan SKU (e.g. B1, P1V2)."""
    try:
        from ._client_factory import web_client_factory
        from azure.mgmt.core.tools import parse_resource_id
        client = web_client_factory(cmd.cli_ctx)
        app = client.web_apps.get(resource_group_name, webapp_name)
        if app and app.server_farm_id:
            plan_parts = parse_resource_id(app.server_farm_id)
            plan = client.app_service_plans.get(plan_parts['resource_group'], plan_parts['name'])
            if plan and plan.sku:
                return plan.sku.name
        return "Unknown"
    except Exception:  # pylint: disable=broad-except
        return "Unknown"


def _determine_deployment_type(params=None, *, src_url=None, artifact_type=None):
    """Infer the deployment mechanism from params object or explicit kwargs.

    When *params* is supplied the values are read from it; explicit kwargs
    override the params-derived values when both are provided.
    """
    _src_url = src_url if src_url is not None else (getattr(params, 'src_url', None) if params else None)
    _artifact = artifact_type if artifact_type is not None else (getattr(params, 'artifact_type', None) if params else None)

    if _src_url:
        return "OneDeploy (URL-based)"
    if _artifact == 'zip':
        return "ZipDeploy"
    if _artifact == 'war':
        return "WarDeploy"
    if _artifact == 'jar':
        return "JarDeploy"
    if _artifact == 'ear':
        return "EarDeploy"
    if _artifact == 'startup':
        return "StartupFile"
    if _artifact == 'static':
        return "StaticDeploy"
    return "OneDeploy"


def build_enriched_error_context(params=None, *, cmd=None, resource_group_name=None,
                                 webapp_name=None, slot=None, src_url=None,
                                 artifact_type=None, status_code=None, error_message=None,
                                 deployment_status=None, deployment_properties=None,
                                 last_known_step=None, kudu_status=None):
    """
    Build a structured context-enriched error dict for a deployment failure.

    Accepts either a *params* object (``OneDeployParams``) **or** individual
    keyword arguments — callers that already have a params object can keep
    passing it; callers in code-paths that don't (e.g. zipdeploy) can pass
    the relevant values directly.  Explicit kwargs override params values.

    Parameters
    ----------
    params : OneDeployParams, optional
        The deployment parameters object.
    cmd, resource_group_name, webapp_name, slot, src_url, artifact_type :
        Individual app-context values; used when *params* is not supplied.
    status_code : int, optional
        HTTP status code of the failed response.
    error_message : str, optional
        Raw error message / response body text.
    deployment_status : str, optional
        Deployment status string (e.g. RuntimeFailed, BuildFailed).
    deployment_properties : dict, optional
        Full deployment properties dict from the status API.
    last_known_step : str, optional
        The last step that completed successfully.
    kudu_status : str, optional
        The SCM/Kudu HTTP status if available.

    Returns
    -------
    dict
        Structured error context ready for display.
    """
    # Normalise — extract from params when available, explicit kwargs win
    _cmd = cmd or (params.cmd if params else None)
    _rg = resource_group_name or (params.resource_group_name if params else None)
    _name = webapp_name or (params.webapp_name if params else None)
    _slot = slot if slot is not None else (getattr(params, 'slot', None) if params else None)
    _src_url = src_url if src_url is not None else (getattr(params, 'src_url', None) if params else None)
    _artifact = artifact_type if artifact_type is not None else (getattr(params, 'artifact_type', None) if params else None)

    pattern = match_failure_pattern(
        status_code=status_code,
        error_message=error_message,
        deployment_status=deployment_status
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
        context["region"] = _get_app_region(_cmd, _rg, _name)
        context["planSku"] = _get_app_plan_sku(_cmd, _rg, _name)
    else:
        context["runtime"] = "Unknown"
        context["region"] = "Unknown"
        context["planSku"] = "Unknown"

    context["deploymentType"] = _determine_deployment_type(
        params, src_url=_src_url, artifact_type=_artifact
    )

    # Causes and fixes
    if pattern:
        context["commonCauses"] = pattern["commonCauses"]
        context["suggestedFixes"] = pattern["suggestedFixes"]
    else:
        context["commonCauses"] = ["Unrecognised failure — see error details below"]
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

    # Instance counts from deployment properties
    if deployment_properties:
        for key in ('numberOfInstancesInProgress', 'numberOfInstancesSuccessful',
                    'numberOfInstancesFailed'):
            val = deployment_properties.get(key)
            if val is not None:
                context.setdefault("instanceStatus", {})[key] = int(val)
        errors = deployment_properties.get('errors')
        if errors:
            context["deploymentErrors"] = [
                {"code": e.get('extendedCode', ''), "message": e.get('message', '')}
                for e in errors[:3]  # cap at 3
            ]
        logs = deployment_properties.get('failedInstancesLogs')
        if logs:
            context["failedInstanceLogs"] = logs[0] if len(logs) == 1 else logs

    # Raw details
    if error_message:
        context["rawError"] = error_message[:500]  # truncate long bodies

    return context


def format_enriched_error_message(context):
    """
    Format the structured context dict into a human-readable error message.

    The output includes the YAML context block and a ready-to-use Copilot prompt.
    """
    lines = []
    lines.append("")
    lines.append("=" * 72)
    lines.append("DEPLOYMENT FAILED — Context-Enriched Diagnostics")
    lines.append("=" * 72)
    lines.append("")

    # YAML context block
    lines.append("--- COPILOT CONTEXT ---")
    lines.append(_safe_yaml_dump(context))
    lines.append("--- END CONTEXT ---")
    lines.append("")

    # Human-readable summary
    lines.append(f"Error Code  : {context.get('errorCode', 'Unknown')}")
    lines.append(f"Stage       : {context.get('stage', 'Unknown')}")
    lines.append(f"Runtime     : {context.get('runtime', 'Unknown')}")
    lines.append(f"Deploy Type : {context.get('deploymentType', 'Unknown')}")
    lines.append(f"Region      : {context.get('region', 'Unknown')}")
    lines.append(f"Plan SKU    : {context.get('planSku', 'Unknown')}")
    lines.append("")

    causes = context.get("commonCauses", [])
    if causes:
        lines.append("Common Causes:")
        for c in causes:
            lines.append(f"  - {c}")
        lines.append("")

    fixes = context.get("suggestedFixes", [])
    if fixes:
        lines.append("Suggested Fixes:")
        for f in fixes:
            lines.append(f"  - {f}")
        lines.append("")

    if context.get("rawError"):
        lines.append(f"Raw Error   : {context['rawError']}")
        lines.append("")

    # Copilot prompt
    lines.append("-" * 72)
    lines.append("Ask Copilot:")
    lines.append('  Copy-paste the COPILOT CONTEXT block above into GitHub Copilot Chat,')
    lines.append('  or run:')
    lines.append('    gh copilot explain "Paste the COPILOT CONTEXT above and explain')
    lines.append('    why this deployment failed and what I should do"')
    lines.append("-" * 72)

    return "\n".join(lines)


def raise_enriched_deployment_error(params=None, *, cmd=None, resource_group_name=None,
                                    webapp_name=None, slot=None, src_url=None,
                                    artifact_type=None, status_code=None, error_message=None,
                                    deployment_status=None, deployment_properties=None,
                                    last_known_step=None, kudu_status=None):
    """
    Build context-enriched diagnostics and raise a CLIError.

    This is the main entry-point called from the deployment code paths.
    Accepts either a *params* object or individual keyword arguments.
    """
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
        deployment_properties=deployment_properties,
        last_known_step=last_known_step,
        kudu_status=kudu_status
    )

    logger.info("Deployment failure context: %s", context)

    message = format_enriched_error_message(context)
    raise CLIError(message)
