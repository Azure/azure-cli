# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Azure CLI changed test selection and regression coverage checks."""

import os
import re

from repository_tools.settings import _MODULE_PATH_PATTERN, _TEST_FILE_PATTERN
from x_engineering_agent.security.sensitive_data import scan_sensitive_content
from x_engineering_agent.tools.github.api import github_get
from x_engineering_agent.tools.github.issues import get_issue
from x_engineering_agent.tools.github.pull_requests import get_pr_changed_files
from x_engineering_agent.tools.sensitive.scanning import (
    scan_issue_for_sensitive_information,
)
from x_engineering_agent.tools.shared.content import (
    SensitiveInformationBlockedError,
    sanitize_untrusted,
)


_RELATED_COMMAND = re.compile(
    r"(?im)^\s*\*\*(Related command|Required scenario test)\*\*"
    r"\s*:?\s*\n\s*`az\s+([a-z0-9-]+(?:\s+[a-z0-9-]+){1,5})`"
)
_ISSUE_SECTION = re.compile(
    r"(?im)^#{2,4}\s*(Describe the bug|To Reproduce|Expected behavior)\s*$"
)
_CODE_FENCE = re.compile(r"(?ms)^[ \t]*```[^\n]*\n.*?^[ \t]*```\s*$")


def _required_commands(pr):
    """Only use commands explicitly identified by the PR as related."""
    body = str((pr or {}).get("body") or "")
    commands = {}
    for match in _RELATED_COMMAND.finditer(body):
        command = "az " + " ".join(match.group(2).split())
        commands[command] = (
            commands.get(command, False)
            or match.group(1).casefold() == "required scenario test"
        )
        if len(commands) >= 10:
            break
    return commands


def _linked_issue_evidence(owner, repo, pr_number, token):
    timeline = github_get(
        f"/repos/{owner}/{repo}/issues/{pr_number}/timeline",
        params={"per_page": 100}, max_pages=10, token=token,
    )
    if timeline["truncated"]:
        raise RuntimeError("PR issue timeline is incomplete; scenario review is required")
    numbers = sorted({
        subject["number"]
        for event in timeline["data"]
        if event.get("event") == "connected"
        if (subject := event.get("subject") or {}).get("repository", {}).get("full_name")
        == f"{owner}/{repo}"
        if isinstance(subject.get("number"), int)
        and subject["number"] > 0 and "pull_request" not in subject
    })
    if len(numbers) > 5:
        raise RuntimeError("Too many linked issues to review scenario evidence completely")
    evidence = []
    for number in numbers:
        issue = get_issue(owner, repo, number, token=token)
        if "pull_request" in issue:
            continue
        if scan_issue_for_sensitive_information(
            owner, repo, number, token=token, issue=issue,
        )["blocked"]:
            raise SensitiveInformationBlockedError(
                f"Sensitive information blocks scenario review for "
                f"{owner}/{repo}#{number}"
            )
        body = _CODE_FENCE.sub("", str(issue.get("body") or ""))[:20_000]
        sections = list(_ISSUE_SECTION.finditer(body))
        requirements = []
        for index, match in enumerate(sections):
            end = sections[index + 1].start() if index + 1 < len(sections) else len(body)
            excerpt = body[match.end():end].strip().split("\n\n", 1)[0].strip()
            if excerpt:
                requirements.append({
                    "section": match.group(1),
                    "excerpt": sanitize_untrusted(excerpt, max_chars=350),
                })
        evidence.append({
            "number": number,
            "url": f"https://github.com/{owner}/{repo}/issues/{number}",
            "title": sanitize_untrusted(str(issue.get("title") or ""), max_chars=200),
            "requirements": requirements,
        })
    return evidence


def _human_scenario_feedback(owner, repo, pr_number, token, paths, head_sha):
    comments = github_get(
        f"/repos/{owner}/{repo}/pulls/{pr_number}/comments",
        params={"per_page": 100}, max_pages=10, token=token,
        sanitize=False,
    )
    if comments["truncated"]:
        raise RuntimeError("PR review comments are incomplete; scenario review is required")
    selected = [
        comment for comment in comments["data"]
        if comment.get("path") in paths
        and (comment.get("user") or {}).get("type") == "User"
        and comment.get("author_association") in {
            "OWNER", "MEMBER", "COLLABORATOR", "CONTRIBUTOR",
        }
        and "scenario test" in str(comment.get("body") or "").casefold()
    ]
    if len(selected) > 20:
        raise RuntimeError("Too many scenario review comments to inspect completely")
    feedback = []
    for comment in selected:
        body = str(comment.get("body") or "")
        if scan_sensitive_content([{
            "location": f"PR review comment {comment.get('id')}",
            "text": body,
        }])["blocked"]:
            raise SensitiveInformationBlockedError(
                f"Sensitive information blocks scenario review for "
                f"{owner}/{repo}#{pr_number}"
            )
        comment_id = comment.get("id")
        if type(comment_id) is not int or comment_id <= 0:
            raise ValueError("Scenario review comment lacks a valid ID")
        prose = " ".join(
            line.strip() for line in body.splitlines()
            if line.strip() and not line.startswith((" ", "\t"))
        )
        feedback.append({
            "id": comment_id,
            "url": (
                f"https://github.com/{owner}/{repo}/pull/{pr_number}"
                f"#discussion_r{comment_id}"
            ),
            "excerpt": sanitize_untrusted(
                prose.replace("@", "(at)"), max_chars=700,
            ),
            "outdated": bool(
                head_sha and comment.get("original_commit_id")
                and comment["original_commit_id"] != head_sha
            ),
        })
    return feedback


def _scenario_evidence(commands, test_files, recording_files, file_changes):
    """Report changed command invocations, not inferred scenario coverage."""
    changes = {
        change["filename"]: change.get("patch")
        for change in file_changes or []
        if change.get("filename") in test_files
    }
    evidence = []
    for command, required in commands.items():
        invocation = re.compile(
            r"(?<![\w-])(?:az\s+)?"
            + r"\s+".join(re.escape(part) for part in command[3:].split())
            + r"(?![\w-])",
            re.I,
        )
        matching_tests = [
            path for path, patch in changes.items()
            if patch is not None and any(
                line.startswith("+") and not line.startswith("+++")
                and invocation.search(line[1:])
                for line in patch.splitlines()
            )
        ]
        status = "needs_review" if matching_tests else "unknown"
        evidence.append({
            "command": command,
            "required": required,
            "status": status,
            "test_files": matching_tests,
            "module_recording_files": recording_files,
        })
    return evidence


def changed_test_files(pr_files):
    """Return changed Azure CLI live-test filename stems."""
    stems = []
    seen = set()
    for path in pr_files or []:
        if not _TEST_FILE_PATTERN.search(path):
            continue
        stem = os.path.basename(path)[:-3]
        if stem not in seen:
            seen.add(stem)
            stems.append(stem)
    return stems


def get_pr_regression_coverage_summary(
    owner, repo, pr_number, token=None, pr_files=None, *,
    pr=None, file_changes=None, issue_evidence=None, review_feedback=None,
):
    """Report changed regression evidence without equating files with scenarios."""
    repo_full = f"{owner}/{repo}"
    files = list(
        pr_files
        if pr_files is not None
        else get_pr_changed_files(owner, repo, pr_number, token=token)
    )
    if repo_full not in {"Azure/azure-cli", "Azure/azure-cli-extensions"}:
        return {
            "applicable": False,
            "gap": False,
            "modules": [],
            "uncovered_modules": [],
            "production_files": [],
            "test_files": [],
            "recording_files": [],
            "scenario_status": "not_applicable",
            "scenario_evidence": [],
            "issue_evidence": [],
            "issue_evidence_status": "not_applicable",
            "review_feedback": [],
        }

    module_root = (
        "src/azure-cli/azure/cli/command_modules/"
        if repo_full == "Azure/azure-cli" else "src/"
    )
    module_pattern = (
        _MODULE_PATH_PATTERN if repo_full == "Azure/azure-cli"
        else re.compile(r"^src/([^/]+)/")
    )
    production_files = [
        path for path in files
        if (
            path.startswith(module_root)
            and path.endswith(".py")
            and "/tests/" not in path
            and os.path.basename(path) not in {"__init__.py", "_help.py"}
        )
    ]
    modules = sorted({
        match.group(1).casefold()
        for path in production_files
        if (match := module_pattern.search(path))
    })
    affected_modules = set(modules)

    def is_affected_module_path(path):
        match = module_pattern.search(path)
        return bool(
            match and match.group(1).casefold() in affected_modules
        )

    test_files = [
        path for path in files
        if (
            path.startswith(module_root)
            and "/tests/" in path
            and os.path.basename(path).startswith("test_")
            and path.endswith(".py")
            and is_affected_module_path(path)
        )
    ]
    recording_files = [
        path for path in files
        if (
            path.startswith(module_root)
            and "/tests/" in path
            and "/recordings/" in path
            and is_affected_module_path(path)
        )
    ]
    covered_modules = {
        match.group(1).casefold()
        for path in test_files + recording_files
        if (match := module_pattern.search(path))
    }
    uncovered_modules = sorted(affected_modules - covered_modules)
    commands = _required_commands(pr)
    if issue_evidence is None:
        if pr and pr.get("number") == pr_number and production_files:
            issue_evidence = _linked_issue_evidence(owner, repo, pr_number, token)
            issue_evidence_status = "linked" if issue_evidence else "not_found"
        else:
            issue_evidence = []
            issue_evidence_status = "not_provided"
    else:
        issue_evidence_status = "provided" if issue_evidence else "not_provided"
    if review_feedback is None:
        review_feedback = (
            _human_scenario_feedback(
                owner, repo, pr_number, token,
                set(production_files + test_files),
                (pr.get("head") or {}).get("sha"),
            )
            if pr and pr.get("number") == pr_number and production_files else []
        )
    scenario_evidence = _scenario_evidence(
        commands, test_files, recording_files, file_changes,
    )
    if not production_files:
        scenario_status = "not_applicable"
    elif issue_evidence or review_feedback or (
        scenario_evidence and all(
            item["status"] == "needs_review" for item in scenario_evidence
        )
    ):
        scenario_status = "needs_review"
    else:
        scenario_status = "unknown"
    return {
        "applicable": bool(production_files),
        "gap": bool(uncovered_modules),
        "modules": modules,
        "uncovered_modules": uncovered_modules,
        "production_files": production_files,
        "test_files": test_files,
        "recording_files": recording_files,
        "scenario_status": scenario_status,
        "scenario_evidence": scenario_evidence,
        "issue_evidence": issue_evidence,
        "issue_evidence_status": issue_evidence_status,
        "review_feedback": review_feedback,
    }


def _live_test_plan(pr_files):
    """Plan selection and skip explanations without dispatching a workflow."""
    paths = [path for path in (pr_files or []) if _TEST_FILE_PATTERN.search(path)]
    runnable = [path for path in paths if "azure-cli-core" not in path.split("/")]
    return {
        "paths": paths,
        "runnable": runnable,
        "skipped_reason": None if runnable else ('PR changes only azure-cli-core unit tests (not runnable by azdev --live)' if paths else 'PR changes no test files (tests/**/test_*.py)'),
        "comment": None if runnable else ("⏭️ **Skipping the live test for this revision because the only test file(s) changed are `azure-cli-core` unit tests**, which the live-test pipeline (`azdev test --live`) does not run — it covers command-module and extension tests only.\n\nThese `azure-cli-core` tests are exercised by upstream CI's unit-test jobs instead. This is informational; no action is required." if paths else '⏭️ **Skipping the live test for this revision because no changed test file was found** (`tests/**/test_*.py`).\n\nThe live-test pipeline runs only the test files a PR changes, so there is nothing to execute for this commit. A skipped live test is not a passing test result. The Agent review separately checks whether the affected command module includes focused regression tests or updated recordings. If a test file is changed in a later commit, the live test will run automatically.'),
        "legacy_title": 'Live Test (Azure CLI PR)',
    }
