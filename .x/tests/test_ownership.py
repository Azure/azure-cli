# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import importlib
import sys
import types
from pathlib import Path

from x_engineering_agent.tools.review_tools.formatting import (
    format_pr_risk_assessment,
)


PACKAGE = Path(__file__).resolve().parents[1]
TOOLS = PACKAGE / "tools"
module = sys.modules.get("repository_tools")
if module is None:
    module = types.ModuleType("repository_tools")
    module.__path__ = [str(TOOLS)]
    sys.modules["repository_tools"] = module
elif str(TOOLS) not in module.__path__:
    module.__path__.append(str(TOOLS))

analysis = importlib.import_module("repository_tools.reviewer.policy.analysis")


def test_aaz_generated_output_requires_verified_aaz_source():
    change = {
        "filename": (
            "src/azure-cli/azure/cli/command_modules/"
            "storage/aaz/latest/storage.py"
        ),
        "additions": 1,
        "deletions": 0,
        "patch": "@@ -1 +1,2 @@\n+generated = True\n",
    }

    findings, _ = analysis._generated_ownership_check(
        "Azure/azure-cli",
        {"body": "https://github.com/Azure/azure-cli/pull/10"},
        [change],
        [change],
        None,
        None,
        [{"repository": "Azure/azure-cli", "valid": True}],
    )
    valid_findings, _ = analysis._generated_ownership_check(
        "Azure/azure-cli",
        {"body": "https://github.com/Azure/aaz/pull/10"},
        [change],
        [change],
        None,
        None,
        [{"repository": "Azure/aaz", "valid": True}],
    )

    assert len(findings) == 1
    assert "Azure/aaz" in findings[0]["summary"]
    assert valid_findings == []


def test_aaz_non_latest_profile_requires_verified_aaz_source():
    change = {
        "filename": (
            "src/azure-cli/azure/cli/command_modules/network/"
            "aaz/2019_03_01_hybrid/network.py"
        ),
        "patch": "@@ -1 +1 @@\n-old\n+new\n",
    }

    findings, _ = analysis._generated_ownership_check(
        "Azure/azure-cli", {}, [change], [change], None, None, [],
    )

    assert len(findings) == 1
    assert "Azure/aaz" in findings[0]["summary"]


def test_risk_assessment_justifies_score_and_requests_owner_review():
    change = {
        "filename": "src/azure-cli/azure/cli/command_modules/role/custom.py",
        "additions": 12,
        "deletions": 2,
        "patch": (
            "@@ -1,2 +1,3 @@\n"
            "+def acquire_managed_identity_token():\n"
            "+    return token\n"
        ),
    }

    risk = analysis._review_risk_assessment(
        "Azure/azure-cli", [change], [change],
    )
    rendered = format_pr_risk_assessment({"risk_assessment": risk})

    assert risk["score"] >= 50
    assert risk["owner_review"] == "required"
    assert "### Risk assessment" in rendered
    assert "Owning-squad review is **required** for `role`" in rendered
    assert "The **High** rating is driven by" in rendered
    assert "- **Change scope:** 1 changed file, 14 changed lines" in rendered
    assert "- **Affected components:** `role`" in rendered
    assert "- **Risk drivers:** security-sensitive behavior (+28)" in rendered
    assert "- **Regression evidence:** No changed regression test" in rendered
    assert "- **Confidence:** High because" in rendered
    assert "- **Required review:**" in rendered


def test_low_risk_assessment_does_not_request_extra_review():
    change = {
        "filename": "doc/authoring_command_modules/README.md",
        "additions": 1,
        "deletions": 0,
        "patch": "@@ -1 +1,2 @@\n+Clarify an example.\n",
    }

    risk = analysis._review_risk_assessment("Azure/azure-cli", [change], [])
    rendered = format_pr_risk_assessment({"risk_assessment": risk})

    assert risk["level"] == "Low"
    assert risk["owner_review"] == "not required"
    assert "no elevated security, reliability, customer, operational" in rendered
    assert "- **Risk drivers:** No elevated risk signal was detected." in rendered
