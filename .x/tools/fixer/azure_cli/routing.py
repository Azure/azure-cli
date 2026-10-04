# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Cross repo routing from Azure CLI to CLI Extensions."""

import requests
import re

from x_engineering_agent.config import (
    BUG_ANALYSIS_DISPATCH_MARKER,
    GITHUB_API,
    MAX_TITLE_CHARS,
)
from x_engineering_agent.tools.github.api import (
    _require_full_workflow,
    github_get,
)
from x_engineering_agent.tools.github.issues import post_comment, create_issue
from x_engineering_agent.tools.github.issues import (
    _trusted_agent_comment_has_marker, get_issue, get_issue_comments, update_comment,
)
from x_engineering_agent.tools.shared.content import (
    SensitiveInformationBlockedError,
)


def create_tracker_issue(src_owner, src_repo, src_issue_number, view, target,
                         token=None):
    """Mirror an Azure CLI issue into its Azure CLI Extensions target."""
    if f"{src_owner}/{src_repo}" != "Azure/azure-cli":
        raise ValueError("Only Azure CLI issues can create extension trackers")
    if (
        target.get("repo") != "Azure/azure-cli-extensions"
        or target.get("kind") != "extension"
        or not isinstance(target.get("name"), str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", target["name"])
    ):
        raise ValueError("Tracker requires a named Azure CLI Extensions target")
    _require_full_workflow(src_owner, src_repo, "tracker creation")
    if view.get("blocked") or (
        view.get("sensitive_information") or {}
    ).get("blocked"):
        raise SensitiveInformationBlockedError(
            "Sensitive information blocks tracker creation for "
            f"{src_owner}/{src_repo}#{src_issue_number}"
        )
    dst_owner, dst_repo = target["repo"].split("/", 1)
    _require_full_workflow(dst_owner, dst_repo, "tracker creation")
    src_url = (
        f"https://github.com/{src_owner}/{src_repo}/issues/"
        f"{src_issue_number}"
    )
    title = f"[{target['name']}] {view['title']}"[:MAX_TITLE_CHARS]
    body = (
        f"Source: {src_url} (by @{view['author']})\n"
        f"Affected extension: `{target['name']}` "
        f"(`src/{target['name']}/`)\n\n"
        f"---\n\n"
        f"{view['prompt_block']}"
    )
    receipt = f"Source: {src_url}"
    comments = get_issue_comments(src_owner, src_repo, src_issue_number, token=token)
    pending = next((
        comment for comment in reversed(comments)
        if _trusted_agent_comment_has_marker(comment, BUG_ANALYSIS_DISPATCH_MARKER)
        and receipt in (comment.get("body") or "")
    ), None)
    if pending:
        linked = re.search(
            r"Tracker: https://github\.com/Azure/azure-cli-extensions/issues/(\d+)",
            pending["body"],
        )
        if linked:
            return get_issue(dst_owner, dst_repo, int(linked.group(1)), token=token)
    else:
        pending = post_comment(
            src_owner, src_repo, src_issue_number,
            f"{receipt}\nExtension handoff pending.\n\n{BUG_ANALYSIS_DISPATCH_MARKER}",
            token=token, role="Fixer",
        )
    existing = github_get(
        f"/repos/{dst_owner}/{dst_repo}/issues",
        params={
            "state": "all", "sort": "created", "direction": "desc", "per_page": 100,
            "since": pending["created_at"],
        },
        max_pages=10, token=token, sanitize=False,
    )
    matches = [
        issue for issue in existing["data"]
        if "pull_request" not in issue
        and (issue.get("body") or "").startswith(receipt + " ")
    ]
    if len(matches) > 1:
        raise RuntimeError("Multiple trackers exist for the source issue")
    if matches:
        new_issue = matches[0]
        update_comment(
            src_owner, src_repo, pending["id"],
            f"{pending['body']}\nTracker: {new_issue['html_url']}", token=token,
        )
        return new_issue
    if existing["truncated"]:
        raise RuntimeError("Extension tracker lookup is incomplete")
    new_issue = create_issue(
        dst_owner, dst_repo, title, body, token=token,
    )
    post_comment(
        src_owner, src_repo, src_issue_number,
        f"{pending['body']}\nTracker: {new_issue['html_url']}",
        token=token, role="Fixer",
    )
    return new_issue