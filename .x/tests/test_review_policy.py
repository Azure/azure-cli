# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Deterministic review policy this package contributes for Azure/azure-cli."""

import importlib
import sys
import types
from pathlib import Path

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

REPOSITORY = "Azure/azure-cli"


def _change(filename, patch=""):
    additions = sum(1 for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
    return {"filename": filename, "patch": patch, "additions": additions, "deletions": 0}


def test_hand_edited_aaz_output_without_source_pr_is_blocked():
    change = _change(
        "src/azure-cli/azure/cli/command_modules/network/aaz/latest/network/vnet/_create.py",
        "@@ -1 +1,2 @@\n+    timeout = 10\n",
    )

    findings, target = analysis._generated_ownership_check(
        REPOSITORY, {"body": "Fixes a bug"}, [change], [change], None, None,
    )

    assert [finding["tool"] for finding in findings] == ["generated-ownership"]
    assert "Azure/aaz" in findings[0]["summary"]
    assert change["filename"] in target["files"]
