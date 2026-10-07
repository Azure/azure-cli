# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Azure CLI pytest failure extraction and repository scope classification."""

from repository_tools.settings import _EXT_PATH_PATTERN, _MODULE_PATH_PATTERN, _PYTEST_FAILED_PATTERN


def extract_failed_tests_from_text(text):
    """Parse failed Azure CLI pytest test IDs from workflow output."""
    if not text:
        return []
    seen = set()
    out = []
    for match in _PYTEST_FAILED_PATTERN.finditer(text):
        path = match.group("path")
        for prefix in ("azure-cli/", "azure-cli-extensions/"):
            if path.startswith(prefix):
                path = path[len(prefix):]
                break
        key = (path, match.group("test_id"))
        if key in seen:
            continue
        seen.add(key)
        out.append({"file": path, "test_id": match.group("test_id")})
    return out


def _scope_key(path):
    """Return an Azure CLI ``(kind, name)`` path scope when recognized."""
    if not path:
        return None
    match = _MODULE_PATH_PATTERN.search(path)
    if match:
        return ("module", match.group(1).lower())
    match = _EXT_PATH_PATTERN.search(path)
    if match:
        name = match.group(1).lower()
        if name not in {"azure-cli", "azure-cli-core", "azure-cli-testsdk"}:
            return ("extension", name)
    return None


def classify_test_failures(failed_tests, pr_files, target=None):
    """Bucket Azure CLI pytest failures by relevance to a pull request."""
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

    relevant = []
    out_of_scope = []
    uncertain = []
    for failure in failed_tests or []:
        path = failure.get("file") or ""
        item = dict(failure)
        if path in pr_file_set:
            item["reason"] = "test file is in the PR diff"
            relevant.append(item)
            continue
        scope = _scope_key(path)
        if scope and scope in pr_scopes:
            kind, name = scope
            item["reason"] = f"same {kind} (`{name}`) as PR changes"
            relevant.append(item)
            continue
        if scope:
            kind, name = scope
            item["reason"] = f"different {kind} (`{name}`) than PR changes"
            out_of_scope.append(item)
            continue
        item["reason"] = "scope could not be inferred from path"
        uncertain.append(item)
    return {
        "pr_relevant": relevant,
        "out_of_scope": out_of_scope,
        "uncertain": uncertain,
    }