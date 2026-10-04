# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Azure CLI review and release-note policy."""

import re

_GENERATED_HISTORY_FILES = {
    "src/azure-cli/HISTORY.rst",
    "src/azure-cli-core/HISTORY.rst",
}


def _is_cli_production_file(repository, path):
    if repository == "Azure/azure-cli":
        return (
            path.startswith((
                "src/azure-cli/azure/cli/command_modules/",
                "src/azure-cli-core/azure/cli/core/",
            ))
            and path.endswith(".py")
        )
    return path.startswith("src/") and path.endswith(".py")


def _cli_review_component(repository, parts):
    if repository == "Azure/azure-cli":
        try:
            return parts[parts.index("command_modules") + 1].casefold()
        except (ValueError, IndexError):
            return None
    if len(parts) > 1 and parts[0].casefold() == "src":
        return parts[1].casefold()
    return None


def _is_cli_hotfix(pr):
    return (
        "hotfix" in str((pr or {}).get("title") or "").casefold()
        and str(((pr or {}).get("base") or {}).get("ref") or "").casefold()
        == "release"
    )


def _is_generated_cli_history(path):
    return path in _GENERATED_HISTORY_FILES


def _generated_history_finding(change, head_repo, head_sha, make_finding):
    return make_finding(
        "release-artifact",
        change,
        "Azure CLI aggregate history is generated from pull-request "
        "metadata and must not be edited directly.",
        "Remove the direct history-file edit. Put one customer-facing "
        "note in the `[Component]` PR title, or put multiple or "
        "overriding notes in the PR description's `History Notes` "
        "section.",
        "Run the PR title/content check and confirm the release-note "
        "generator derives the intended entry from PR metadata.",
        head_repo=head_repo,
        head_sha=head_sha,
    )


def _cli_release_findings(
    pr_title, is_hotfix, release_changes, customer_visible_changes,
    head_repo, head_sha, make_finding, pr_body="",
):
    if not customer_visible_changes:
        return []
    change = customer_visible_changes[0]
    if is_hotfix and not release_changes:
        return [make_finding(
            "release-artifact",
            change,
            "Customer-visible Azure CLI hotfix behavior changed without the "
            "manual history entry required for hotfix PRs.",
            "Add the customer-facing note directly to the appropriate Azure "
            "CLI or Core `HISTORY.rst` file because regular history "
            "generation intentionally ignores hotfix PRs.",
            "Run history validation and confirm the hotfix entry appears in "
            "the release history.",
            head_repo=head_repo,
            head_sha=head_sha,
        )]
    history_notes = re.search(
        r"\*\*History Notes\*\*",
        pr_body,
    )
    populated_notes = False
    if history_notes:
        section = pr_body[history_notes.end():].split("---", 1)[0]
        populated_notes = bool(re.search(
            r"(?m)^\s*\[(?!Component\])[^]\r\n]+\]\s+\S.+", section,
        ))
    if not is_hotfix and not pr_title.startswith("[") and not populated_notes:
        return [make_finding(
            "release-artifact",
            change,
            "Customer-visible Azure CLI behavior is not marked for generated "
            "release notes in the PR metadata.",
            "Start the PR title with `[Component]` and describe the "
            "customer-facing change there. For multiple or overriding notes, "
            "use the PR description's `History Notes` section.",
            "Run the PR title/content check and confirm the metadata is "
            "accepted for automatic history generation.",
            head_repo=head_repo,
            head_sha=head_sha,
        )]
    return []


def _cli_command_checks():
    return (
        "Validate Azure CLI help style and that every new or changed "
        "public command has a runnable example."
    )
