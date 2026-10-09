# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import importlib
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from x_engineering_agent.tools.live_tests.formatting import format_test_validation
from x_engineering_agent.tools.shared.content import SensitiveInformationBlockedError


PACKAGE = Path(__file__).resolve().parents[1]
TOOLS = PACKAGE / "tools"
module = sys.modules.get("repository_tools")
if module is None:
    module = types.ModuleType("repository_tools")
    module.__path__ = [str(TOOLS)]
    sys.modules["repository_tools"] = module
elif str(TOOLS) not in module.__path__:
    module.__path__.append(str(TOOLS))

live_tests = importlib.import_module("repository_tools.tester.azure_cli.live_tests")
analysis = importlib.import_module("repository_tools.reviewer.policy.analysis")


_VM_PRODUCTION = "src/azure-cli/azure/cli/command_modules/vm/custom.py"
_VM_TEST = (
    "src/azure-cli/azure/cli/command_modules/vm/tests/latest/test_vm_commands.py"
)
_VM_RECORDING = (
    "src/azure-cli/azure/cli/command_modules/vm/tests/latest/"
    "recordings/test_vm_boot_diagnostics.yaml"
)
_BOOT_LOG_PR = {
    "body": "**Related command**\n`az vm boot-diagnostics get-boot-log`\n\n"
            "**Testing Guide**\nCustom (non-managed) storage account boot log.",
}


def _vm_coverage(changes, *, pr=_BOOT_LOG_PR, issue_evidence=None,
                 review_feedback=None):
    return live_tests.get_pr_regression_coverage_summary(
        "Azure", "azure-cli", 33727, pr_files=[
            _VM_PRODUCTION, *(change["filename"] for change in changes)
        ], pr=pr, file_changes=changes, issue_evidence=issue_evidence,
        review_feedback=review_feedback,
    )


def test_scenario_invocation_and_recording_do_not_claim_variant_coverage():
    changes = [
        {"filename": _VM_TEST, "patch": (
            "@@ -1,0 +1,2 @@\n"
            "+def test_vm_boot_diagnostics(self):\n"
            "+    self.cmd('vm boot-diagnostics get-boot-log -g {rg} -n {vm}')\n"
        )},
        {"filename": _VM_RECORDING, "patch": "+CommandName: vm boot-diagnostics get-boot-log"},
    ]
    coverage = _vm_coverage(changes)
    assert coverage["gap"] is False
    assert coverage["scenario_status"] == "needs_review"
    assert coverage["scenario_evidence"] == [{
        "command": "az vm boot-diagnostics get-boot-log",
        "required": False,
        "status": "needs_review",
        "test_files": [_VM_TEST],
        "module_recording_files": [_VM_RECORDING],
    }]
    rendered = format_test_validation({"review_only": True}, coverage)
    assert "Scenario coverage is unverified" in rendered
    assert "invocation alone does not verify" in rendered
    assert "Present for" not in rendered
    summary = analysis.analyze_review_tools(
        "Azure/azure-cli", _BOOT_LOG_PR,
        [{"filename": _VM_PRODUCTION}, *changes],
    )
    checks = next(
        target["checks"] for target in summary["review_targets"]
        if target["tool"] == "test-strength"
    )
    assert any("fixtures and assertions" in check for check in checks)


def test_unrelated_changed_test_is_unknown_even_when_scenario_required():
    coverage = _vm_coverage([{
        "filename": _VM_TEST,
        "patch": "@@ -1,0 +1 @@\n+    self.cmd('vm image list')\n",
    }], pr={
        "body": "**Required scenario test**\n"
                "`az vm boot-diagnostics get-boot-log`",
    })
    assert coverage["scenario_status"] == "unknown"
    assert coverage["gap"] is False
    assert coverage["uncovered_modules"] == []
    rendered = format_test_validation({}, coverage)
    assert "Scenario coverage is unverified" in rendered
    assert "without a focused test or recording change" not in rendered


def test_related_command_without_explicit_requirement_is_unknown():
    coverage = _vm_coverage([{
        "filename": _VM_TEST,
        "patch": "+    self.cmd('vm image list')",
    }])
    assert coverage["scenario_status"] == "unknown"
    assert coverage["gap"] is False


def test_helper_or_recording_can_cover_command_without_direct_test_invocation():
    helper = _vm_coverage([{
        "filename": _VM_TEST,
        "patch": "+    self.verify_custom_storage_boot_log()",
    }], pr={
        "body": "**Required scenario test**\n"
                "`az vm boot-diagnostics get-boot-log`",
    })
    recorded = _vm_coverage([{"filename": _VM_RECORDING}], pr={
        "body": "**Required scenario test**\n"
                "`az vm boot-diagnostics get-boot-log`",
    })
    assert helper["scenario_status"] == "unknown"
    assert recorded["scenario_status"] == "unknown"
    assert helper["gap"] is False
    assert recorded["gap"] is False


def test_missing_patch_or_unspecified_scenario_is_unknown_not_missing():
    missing_patch = _vm_coverage([{"filename": _VM_TEST}])
    unspecified = _vm_coverage(
        [{"filename": _VM_TEST, "patch": "+    self.cmd('vm image list')"}],
        pr={"body": ""},
    )
    assert missing_patch["scenario_status"] == "unknown"
    assert missing_patch["gap"] is False
    assert unspecified["scenario_status"] == "unknown"
    assert unspecified["gap"] is False
    assert "Scenario coverage is unverified" in format_test_validation(
        {"review_only": True}, unspecified,
    )


def test_linked_issue_without_pr_command_still_requires_scenario_review():
    coverage = _vm_coverage(
        [{"filename": _VM_TEST}], pr={"body": ""},
        issue_evidence=[{
            "number": 33556,
            "url": "https://github.com/Azure/azure-cli/issues/33556",
            "title": "VM boot log fails",
            "requirements": [{"section": "Describe the bug",
                              "excerpt": "Custom storage account fails."}],
        }],
    )
    assert coverage["scenario_status"] == "needs_review"
    assert coverage["gap"] is False
    assert "Custom storage account fails" in format_test_validation(
        {"review_only": True}, coverage,
    )


def test_linked_issue_scenario_surfaces_conditions_and_expected_output():
    issue = {
        "number": 33556,
        "title": "az vm boot-diagnostics get-boot-log fails",
        "body": (
            "### Describe the bug\n\n"
            "`az vm boot-diagnostics get-boot-log` crashes when the VM uses "
            "a custom (non-managed) storage account.\n\n"
            "```python\nirrelevant = 'code'\n```\n\n"
            "### Expected behavior\n\n"
            "The command should print boot log on stdout.\n\n"
            "### Environment Summary\n\nUnrelated debug output."
        ),
    }
    timeline = {"data": [
        {"event": "connected", "subject": {
            "number": 33556, "repository": {"full_name": "Azure/azure-cli"},
        }},
        {"event": "connected", "subject": {
            "number": 42, "repository": {"full_name": "Someone/else"},
        }},
    ], "truncated": False}
    changes = [{"filename": _VM_TEST, "patch": (
        "+    self.cmd('vm boot-diagnostics get-boot-log -g {rg} -n {vm}')"
    )}]
    with (
        patch.object(live_tests, "github_get",
                     side_effect=[timeline, {"data": [], "truncated": False}]) as linked,
        patch.object(live_tests, "scan_issue_for_sensitive_information",
                     return_value={"blocked": False}) as scan,
        patch.object(live_tests, "get_issue", return_value=issue) as fetch,
    ):
        coverage = _vm_coverage(changes, pr={
            **_BOOT_LOG_PR, "number": 33727,
        })
    assert linked.call_count == 2
    scan.assert_called_once_with(
        "Azure", "azure-cli", 33556, token=None, issue=issue,
    )
    fetch.assert_called_once_with("Azure", "azure-cli", 33556, token=None)
    assert coverage["scenario_status"] == "needs_review"
    assert coverage["gap"] is False
    assert coverage["issue_evidence"][0]["number"] == 33556
    rendered = format_test_validation({"review_only": True}, coverage)
    assert "custom (non-managed) storage account" in rendered
    assert "print boot log on stdout" in rendered
    assert "irrelevant" not in rendered
    assert "https://github.com/Azure/azure-cli/issues/33556" in rendered


def test_issue_lookup_errors_and_incomplete_timeline_do_not_pass_silently():
    with patch.object(live_tests, "github_get", return_value={"data": [], "truncated": True}):
        with pytest.raises(RuntimeError, match="incomplete"):
            _vm_coverage([], pr={**_BOOT_LOG_PR, "number": 33727})
    with patch.object(live_tests, "github_get", side_effect=ConnectionError("GitHub unavailable")):
        with pytest.raises(ConnectionError, match="GitHub unavailable"):
            _vm_coverage([], pr={**_BOOT_LOG_PR, "number": 33727})


def test_no_linked_issue_is_explicitly_unverified():
    with patch.object(
        live_tests,
        "github_get",
        side_effect=[
            {"data": [], "truncated": False},
            {"data": [], "truncated": False},
        ],
    ):
        coverage = _vm_coverage([{"filename": _VM_TEST}], pr={
            **_BOOT_LOG_PR, "number": 33727,
        })
    assert coverage["scenario_status"] == "unknown"
    assert coverage["issue_evidence_status"] == "not_found"
    assert "No linked issue was found" in format_test_validation(
        {"review_only": True}, coverage,
    )


def test_sensitive_linked_issue_is_not_exposed():
    timeline = {"data": [{"event": "connected", "subject": {
        "number": 33556, "repository": {"full_name": "Azure/azure-cli"},
    }}], "truncated": False}
    with (
        patch.object(live_tests, "github_get", return_value=timeline),
        patch.object(live_tests, "get_issue", return_value={"number": 33556, "body": "redacted"}),
        patch.object(live_tests, "scan_issue_for_sensitive_information",
                     return_value={"blocked": True}),
    ):
        with pytest.raises(SensitiveInformationBlockedError):
            _vm_coverage([], pr={**_BOOT_LOG_PR, "number": 33727})


def test_human_review_calls_out_managed_and_custom_output_checks():
    body = (
        "@copilot This should've been caught by a scenario test. "
        "The managed storage scenario should also be tested by a scenario "
        "test; it just tests that it turns on.\n\n"
        " self.cmd('vm boot-diagnostics enable -g {rg} -n {vm}')\n"
        " self.cmd('vm boot-diagnostics get-boot-log -g {rg} -n {vm}')\n\n"
        "It doesn't get the diagnostic logs after enabling managed storage."
    )
    comment = {
        "id": 3800328667,
        "body": body,
        "path": _VM_PRODUCTION,
        "user": {"type": "User", "login": "JaysonTaiMicrosoft"},
        "author_association": "CONTRIBUTOR",
        "original_commit_id": "older-head",
    }
    with patch.object(
        live_tests,
        "github_get",
        side_effect=[
            {"data": [], "truncated": False},
            {"data": [comment], "truncated": False},
        ],
    ):
        coverage = _vm_coverage([{"filename": _VM_TEST}], pr={
            "number": 33727, "body": "",
            "head": {"sha": "current-head"},
        })
    assert coverage["scenario_status"] == "needs_review"
    assert coverage["gap"] is False
    assert coverage["review_feedback"][0]["outdated"] is True
    rendered = format_test_validation({"review_only": True}, coverage)
    assert "managed storage scenario" in rendered
    assert "doesn't get the diagnostic logs" in rendered
    assert "latest diff" in rendered
    assert "discussion_r3800328667" in rendered
    assert "@copilot" not in rendered


def test_issue_and_human_feedback_keep_both_storage_paths_unverified():
    coverage = _vm_coverage(
        [{"filename": _VM_TEST, "patch": (
            "+    self.cmd('vm boot-diagnostics get-boot-log -g {rg} -n {vm}')"
        )}],
        issue_evidence=[{
            "number": 33556,
            "url": "https://github.com/Azure/azure-cli/issues/33556",
            "title": "Boot log error",
            "requirements": [
                {"section": "Describe the bug",
                 "excerpt": "VM with custom (non-managed) storage fails."},
                {"section": "Expected behavior",
                 "excerpt": "Print the boot log output."},
            ],
        }],
        review_feedback=[{
            "id": 3800328667,
            "url": (
                "https://github.com/Azure/azure-cli/pull/33727"
                "#discussion_r3800328667"
            ),
            "excerpt": (
                "Managed storage scenario should test actual get-boot-log "
                "output, not only that diagnostics turns on."
            ),
        }],
    )
    assert coverage["scenario_status"] == "needs_review"
    assert coverage["gap"] is False
    rendered = format_test_validation({"review_only": True}, coverage)
    assert "custom (non-managed) storage" in rendered
    assert "Managed storage scenario" in rendered
    assert "Print the boot log output" in rendered
    assert "Scenario coverage is unverified" in rendered


def test_bot_or_unrelated_review_is_not_scenario_feedback():
    comments = [
        {"id": 1, "path": _VM_PRODUCTION, "body": "scenario test",
         "user": {"type": "Bot"}, "author_association": "MEMBER"},
        {"id": 2, "path": _VM_PRODUCTION.replace("/vm/", "/storage/"),
         "body": "scenario test", "user": {"type": "User"},
         "author_association": "MEMBER"},
    ]
    with patch.object(
        live_tests,
        "github_get",
        side_effect=[
            {"data": [], "truncated": False},
            {"data": comments, "truncated": False},
        ],
    ):
        coverage = _vm_coverage([], pr={"number": 33727, "body": ""})
    assert coverage["review_feedback"] == []
    assert coverage["scenario_status"] == "unknown"


def test_sensitive_review_feedback_and_incomplete_comments_fail_explicitly():
    comment = {
        "id": 3800328667, "path": _VM_PRODUCTION,
        "body": "Scenario test requires github_pat_" + "A" * 24,
        "user": {"type": "User"}, "author_association": "CONTRIBUTOR",
    }
    with patch.object(
        live_tests,
        "github_get",
        side_effect=[
            {"data": [], "truncated": False},
            {"data": [comment], "truncated": False},
        ],
    ):
        with pytest.raises(SensitiveInformationBlockedError):
            _vm_coverage([], pr={"number": 33727, "body": ""})
    with patch.object(
        live_tests,
        "github_get",
        side_effect=[
            {"data": [], "truncated": False},
            {"data": [], "truncated": True},
        ],
    ):
        with pytest.raises(RuntimeError, match="comments are incomplete"):
            _vm_coverage([], pr={"number": 33727, "body": ""})


def test_module_gap_is_reported_for_uncovered_production_module():
    other_test = _VM_TEST.replace("/vm/", "/compute/")
    gap = _vm_coverage([{"filename": other_test}])
    assert gap["uncovered_modules"] == ["vm"]
    assert gap["gap"] is True
    assert gap["scenario_status"] == "unknown"
    assert "without a focused test or recording change" in format_test_validation(
        {}, gap,
    )
