# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Azure CLI module and extension target discovery and inference."""

import re

import requests

from repository_tools.settings import _AZ_CMD_PATTERN, _EXT_PATH_PATTERN, _MODULE_PATH_PATTERN
from x_engineering_agent.tools.targets.discovery import (
    _list_repo_dirs,
    _target_list_cache,
)


def list_azure_cli_modules(branch="dev", token=None, refresh=False):
    """Names of core command modules in Azure/azure-cli."""
    key = ("modules", branch)
    if refresh or key not in _target_list_cache:
        _target_list_cache[key] = _list_repo_dirs(
            "Azure", "azure-cli",
            "src/azure-cli/azure/cli/command_modules", branch, token,
        )
    return _target_list_cache[key]


def list_azure_cli_extensions(branch="main", token=None, refresh=False):
    """Names of extensions in Azure/azure-cli-extensions."""
    key = ("extensions", branch)
    if refresh or key not in _target_list_cache:
        _target_list_cache[key] = _list_repo_dirs(
            "Azure", "azure-cli-extensions", "src", branch, token,
        )
    return _target_list_cache[key]


def _normalize_name(name):
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def resolve_target(candidate, token=None):
    """Map a candidate to an Azure CLI module or extension target."""
    if not candidate:
        return {"kind": "unknown", "name": None, "repo": None}
    try:
        modules = list_azure_cli_modules(token=token)
        extensions = list_azure_cli_extensions(token=token)
    except requests.HTTPError:
        return {"kind": "unknown", "name": candidate, "repo": None}
    if candidate in extensions:
        return {
            "kind": "extension", "name": candidate,
            "repo": "Azure/azure-cli-extensions",
        }
    if candidate in modules:
        return {
            "kind": "module", "name": candidate,
            "repo": "Azure/azure-cli",
        }
    norm = _normalize_name(candidate)
    for extension in extensions:
        if _normalize_name(extension) == norm:
            return {
                "kind": "extension", "name": extension,
                "repo": "Azure/azure-cli-extensions",
            }
    for module in modules:
        if _normalize_name(module) == norm:
            return {
                "kind": "module", "name": module,
                "repo": "Azure/azure-cli",
            }
    return {"kind": "unknown", "name": candidate, "repo": None}


def _candidate_scores(text, weight=1):
    scores = {}
    if not text:
        return scores
    for pattern in (_MODULE_PATH_PATTERN, _EXT_PATH_PATTERN, _AZ_CMD_PATTERN):
        for match in pattern.finditer(text):
            name = match.group(1).lower()
            scores[name] = scores.get(name, 0) + weight
    return scores


def infer_target(text=None, pr_files=None, token=None):
    """Pick the most likely Azure CLI module or extension target."""
    if pr_files:
        file_scores = _candidate_scores("\n".join(pr_files), weight=5)
        for name in sorted(file_scores, key=lambda item: -file_scores[item]):
            target = resolve_target(name, token=token)
            if target["kind"] != "unknown":
                return target
        return {"kind": "none", "name": None, "repo": None}

    text_scores = _candidate_scores(text or "", weight=1)
    for name in sorted(text_scores, key=lambda item: -text_scores[item]):
        target = resolve_target(name, token=token)
        if target["kind"] != "unknown":
            return target
    return {"kind": "unknown", "name": None, "repo": None}


def _live_test_target(text, pr_files, module=None, target_kind=None, token=None):
    """Resolve the command target for the live-test runner."""
    if module:
        resolved = resolve_target(module, token=token)
        if resolved["kind"] != "unknown":
            module = resolved["name"]
            target_kind = target_kind or resolved["kind"]
    else:
        resolved = infer_target(text=text, pr_files=pr_files, token=token)
        if resolved["kind"] in ("module", "extension"):
            module = resolved["name"]
            target_kind = target_kind or resolved["kind"]
    return {"module": module, "target_kind": target_kind or 'module'}


def _infer_repository_target(text=None, pr_files=None, token=None):
    """Preserve repository-wide inference when no changed files identify a module."""
    target = infer_target(text=text, pr_files=pr_files, token=token)
    if pr_files == [] and target["kind"] == "unknown":
        return {"kind": "repository", "name": None, "repo": "Azure/azure-cli"}
    return target
