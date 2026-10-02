# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Durable Foundry AAZ source jobs and upstream source pull request discovery."""

import requests

from repository_tools.settings import AAZ_SOURCE_REPOSITORY
from x_engineering_agent.config import AAZ_SOURCE_FORK, GITHUB_API
from x_engineering_agent.tools.github.api import github_get


def start_aaz_source_task(issue_number, downstream_pr_url, changed_files,
                          prompt_context, token=None):
    """Queue the durable AAZ source change required by generated CLI output."""
    from x_engineering_agent.tools.copilot.execution import submit_aaz_source

    return submit_aaz_source(
        issue_number, downstream_pr_url, changed_files,
        prompt_context, token=token,
    )


def find_aaz_fork_prs_ready_for_promotion(token=None, limit=30):
    """Compatibility hook: Foundry publishes AAZ jobs without staging PRs."""
    return []


def promote_aaz_fork_pr(fork_pr_number, title, body, token=None):
    """Reject retired staging promotion rather than bypass durable publication."""
    raise RuntimeError("Foundry AAZ jobs publish directly without a staging PR.")


def find_promoted_aaz_source_pr(issue_number, token=None):
    """Return the open upstream AAZ PR created for an Agent issue."""
    owner, repo = AAZ_SOURCE_REPOSITORY.split("/", 1)
    response = github_get(
        f"/repos/{owner}/{repo}/pulls",
        params={"state": "all", "sort": "created",
                "direction": "desc", "per_page": 100},
        max_pages=1, token=token, sanitize=False,
    )
    fragment = f"-issue-{issue_number}-"
    return next(
        (
            pull_request for pull_request in response["data"]
            if fragment in (
                (pull_request.get("head") or {}).get("ref") or ""
            )
            and (
                pull_request.get("state") == "open"
                or bool(pull_request.get("merged_at"))
            )
            and (
                (
                    (pull_request.get("head") or {}).get("repo") or {}
                ).get("full_name") == AAZ_SOURCE_FORK
            )
        ),
        None,
    )
