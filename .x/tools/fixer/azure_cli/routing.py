# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Cross repo routing from Azure CLI to CLI Extensions."""

import requests

from x_engineering_agent.config import (
    BUG_ANALYSIS_MARKER,
    GITHUB_API,
    MAX_TITLE_CHARS,
)
from x_engineering_agent.tools.github.api import (
    _require_full_workflow,
)
from x_engineering_agent.tools.github.issues import post_comment, create_issue
from x_engineering_agent.tools.shared.content import (
    SensitiveInformationBlockedError,
)


def create_tracker_issue(src_owner, src_repo, src_issue_number, view, target,
                         token=None):
    """Mirror an Azure CLI issue into its Azure CLI Extensions target."""
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
    new_issue = create_issue(
        dst_owner, dst_repo, title, body, token=token,
    )
    post_comment(
        src_owner, src_repo, src_issue_number,
        f"Routed to {target['repo']} as #{new_issue['number']} "
        f"({new_issue['html_url']}) because this targets the "
        f"`{target['name']}` extension, whose source lives in "
        f"`Azure/azure-cli-extensions`.\n\n{BUG_ANALYSIS_MARKER}",
        token=token,
        role="Fixer",
    )
    return new_issue