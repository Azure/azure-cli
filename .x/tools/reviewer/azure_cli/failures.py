# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Azure CLI pytest failure extraction and repository scope classification."""

from repository_tools.settings import _EXT_PATH_PATTERN, _MODULE_PATH_PATTERN, _PYTEST_FAILED_PATTERN

CORE_SCOPE = ("core", "azure-cli-core")
_NON_SCOPED_PACKAGES = {"azure-cli", "azure-cli-testsdk"}


def _normalize_test_path(path):
    path = str(path or "")
    for prefix in ("azure-cli/", "azure-cli-extensions/"):
        if path.startswith(prefix):
            return path[len(prefix):]
    return path


def extract_failed_tests_from_text(text):
    """Parse failed Azure CLI pytest test IDs from workflow output."""
    if not text:
        return []
    seen = set()
    out = []
    for match in _PYTEST_FAILED_PATTERN.finditer(text):
        path = _normalize_test_path(match.group("path"))
        key = (path, match.group("test_id"))
        if key in seen:
            continue
        seen.add(key)
        out.append({"file": path, "test_id": match.group("test_id")})
    return out


def _scope_key(path):
    """Azure CLI (kind, name) path scope; azure-cli-core maps to core."""
    if not path:
        return None
    match = _MODULE_PATH_PATTERN.search(path)
    if match:
        return ("module", match.group(1).lower())
    match = _EXT_PATH_PATTERN.search(path)
    if match:
        name = match.group(1).lower()
        if name == CORE_SCOPE[1]:
            return CORE_SCOPE
        if name not in _NON_SCOPED_PACKAGES:
            return ("extension", name)
    return None


def _test_keys(items):
    return {
        (_normalize_test_path(item.get("file")), str(item.get("test_id") or ""))
        for item in items or []
        if isinstance(item, dict) and item.get("file") and item.get("test_id")
    }


def classify_test_failures(failed_tests, pr_files, target=None, base_results=None):
    """Bucket Azure CLI pytest failures by relevance to a pull request.

    An out-of-scope failure is pre-existing only if it also fails on base; otherwise unverified.
    """
    pr_file_set = set(pr_files or [])
    pr_scopes = {
        scope
        for path in (pr_files or [])
        if (scope := _scope_key(path))
    }
    if (
        not pr_scopes
        and target
        and target.get("kind") in ("module", "extension")
        and target.get("name")
    ):
        pr_scopes.add((target["kind"], target["name"].lower()))
    core_changed = CORE_SCOPE in pr_scopes

    base_results = base_results or {}
    base_ref = str(base_results.get("ref") or "the base branch")
    base_failed = _test_keys(base_results.get("failed"))
    base_passed = _test_keys(base_results.get("passed"))

    relevant = []
    out_of_scope = []
    unverified = []
    uncertain = []
    for failure in failed_tests or []:
        path = failure.get("file") or ""
        item = dict(failure)
        key = (_normalize_test_path(path), str(failure.get("test_id") or ""))
        on_base = (
            "failed" if key in base_failed
            else "passed" if key in base_passed
            else None
        )
        if on_base:
            item["base_result"] = on_base
        if path in pr_file_set:
            item["reason"] = "test file is in the PR diff"
            if on_base == "failed":
                item["reason"] += f"; also fails on base `{base_ref}`"
            relevant.append(item)
            continue
        scope = _scope_key(path)
        if scope and scope in pr_scopes:
            kind, name = scope
            item["reason"] = f"same {kind} (`{name}`) as PR changes"
            if on_base == "failed":
                item["reason"] += f"; also fails on base `{base_ref}`"
            relevant.append(item)
            continue
        if on_base == "failed":
            where = (
                f"different {scope[0]} (`{scope[1]}`) than PR changes"
                if scope else "scope could not be inferred from path"
            )
            item["reason"] = (
                f"{where}; also fails on base `{base_ref}` (pre-existing)"
            )
            out_of_scope.append(item)
            continue
        if on_base == "passed":
            where = (
                f"different {scope[0]} (`{scope[1]}`) than PR changes"
                if scope else "scope could not be inferred from path"
            )
            item["reason"] = (
                f"{where}, but passes on base `{base_ref}`; the failure is "
                "new on the PR head"
            )
            uncertain.append(item)
            continue
        if scope and core_changed:
            kind, name = scope
            item["reason"] = (
                f"different {kind} (`{name}`), but the PR changes "
                "`azure-cli-core`, which it depends on; not confirmed on base"
            )
            uncertain.append(item)
            continue
        if scope:
            kind, name = scope
            item["reason"] = (
                f"different {kind} (`{name}`) than PR changes; unverified — "
                "not confirmed on base, so not labelled pre-existing or flaky"
            )
            unverified.append(item)
            continue
        item["reason"] = "scope could not be inferred from path"
        uncertain.append(item)
    return {
        "pr_relevant": relevant,
        "out_of_scope": out_of_scope,
        "unverified": unverified,
        "uncertain": uncertain,
    }
