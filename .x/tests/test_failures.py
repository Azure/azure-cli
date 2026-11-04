# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import importlib
import sys
import types
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
TOOLS = PACKAGE / "tools"


def _repository_tools():
    module = sys.modules.get("repository_tools")
    if module is None:
        module = types.ModuleType("repository_tools")
        module.__path__ = [str(TOOLS)]
        sys.modules["repository_tools"] = module
    elif str(TOOLS) not in module.__path__:
        module.__path__.append(str(TOOLS))
    return module


_repository_tools()
failures = importlib.import_module("repository_tools.reviewer.azure_cli.failures")

STORAGE_SRC = "src/azure-cli/azure/cli/command_modules/storage/custom.py"
STORAGE_TEST = "src/azure-cli/azure/cli/command_modules/storage/tests/latest/test_blob.py"
NETWORK_TEST = "src/azure-cli/azure/cli/command_modules/network/tests/latest/test_nsg.py"
CORE_SRC = "src/azure-cli-core/azure/cli/core/commands/__init__.py"
CORE_TEST = "src/azure-cli-core/azure/cli/core/tests/test_help.py"
BUCKETS = ("pr_relevant", "out_of_scope", "unverified", "uncertain")


def _failure(path, test_id="test_x"):
    return {"file": path, "test_id": test_id}


@pytest.mark.parametrize(("failure", "base", "bucket", "reason"), [
    (_failure(NETWORK_TEST), None, "unverified", "not confirmed on base"),
    (_failure(NETWORK_TEST), {"ref": "dev", "failed": [_failure("azure-cli/" + NETWORK_TEST)]},
     "out_of_scope", "also fails on base `dev` (pre-existing)"),
    (_failure(NETWORK_TEST), {"ref": "dev", "passed": [_failure(NETWORK_TEST)]},
     "uncertain", "passes on base `dev`"),
    (_failure(NETWORK_TEST), {"ref": "dev", "failed": [_failure(NETWORK_TEST, "test_other")]},
     "unverified", "not confirmed on base"),
    (_failure(STORAGE_TEST), {"ref": "dev", "failed": [_failure(STORAGE_TEST)]},
     "pr_relevant", "also fails on base `dev`"),
])
def test_failures_need_base_evidence_before_being_called_pre_existing(failure, base, bucket, reason):
    result = failures.classify_test_failures([failure], [STORAGE_SRC], base_results=base)
    assert [item["file"] for item in result[bucket]] == [failure["file"]]
    assert reason in result[bucket][0]["reason"]
    assert sum(len(result[key]) for key in BUCKETS) == 1


def test_core_change_puts_core_tests_in_scope_and_other_modules_uncertain():
    result = failures.classify_test_failures(
        [_failure(CORE_TEST), _failure(NETWORK_TEST)], [CORE_SRC],
    )
    assert [item["file"] for item in result["pr_relevant"]] == [CORE_TEST]
    assert "same core (`azure-cli-core`)" in result["pr_relevant"][0]["reason"]
    assert [item["file"] for item in result["uncertain"]] == [NETWORK_TEST]
    assert "azure-cli-core" in result["uncertain"][0]["reason"]
    assert result["out_of_scope"] == [] and result["unverified"] == []
