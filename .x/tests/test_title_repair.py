# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import importlib
import sys
import types
from pathlib import Path


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
title_repair = importlib.import_module("repository_tools.fixer.title_gate.title_repair")
targets = importlib.import_module("repository_tools.fixer.azure_cli.targets")


def test_repaired_title_strips_stray_delimiters_after_command():
    assert title_repair.repaired_pr_title(
        "Azure/azure-cli",
        (
            "[AppService] `az appservice plan create`: ] - "
            "Fix Windows defaults"
        ),
        component="appservice",
    ) == (
        "[AppService] `az appservice plan create`: Fix Windows defaults"
    )


def test_repaired_title_omits_command_with_embedded_parameter():
    assert title_repair.repaired_pr_title(
        "Azure/azure-cli",
        (
            "[Packaging] Fix #34131: `az --version`: "
            "Enable Fedora 44 RPM build and validation"
        ),
        component="packaging",
    ) == (
        "[Packaging] Fix #34131: Enable Fedora 44 RPM build and validation"
    )


def test_component_comes_from_changed_production_module_not_test_or_issue_text():
    files = [
        "src/azure-cli/azure/cli/command_modules/network/_params.py",
        "src/azure-cli/azure/cli/command_modules/storage/tests/latest/test_storage.py",
    ]
    assert title_repair.expected_cli_title_component(files) == "Network"
    assert not title_repair.cli_title_component_matches(
        "[Storage] Fix #33825: Correct address lookup", files,
    )
    assert title_repair.cli_title_component_matches(
        "[Network] Fix #33825: Correct address lookup", files,
    )
    assert title_repair.expected_cli_title_component(
        files + ["src/azure-cli/azure/cli/command_modules/storage/custom.py"],
    ) is None


def test_historical_webapp_component_uses_release_note_display_name():
    files = [
        "src/azure-cli/azure/cli/command_modules/appservice/custom.py",
        "src/azure-cli/azure/cli/command_modules/appservice/tests/latest/test_webapp_commands_thru_mock.py",
    ]
    assert title_repair.expected_cli_title_component(files) == "AppService"
    assert not title_repair.cli_title_component_matches(
        "[appservice] Surface Kudu 409 response body in "
        "`az webapp webjob triggered list`", files,
    )


def test_unresolved_cli_issue_uses_repository_target(monkeypatch):
    monkeypatch.setattr(
        targets,
        "infer_target",
        lambda **kwargs: {"kind": "unknown", "name": None, "repo": None},
    )

    assert targets._infer_repository_target(
        text="Windows packaging launcher failure",
        pr_files=[],
    ) == {
        "kind": "repository",
        "name": None,
        "repo": "Azure/azure-cli",
    }


def test_resolved_cli_issue_keeps_module_target(monkeypatch):
    monkeypatch.setattr(
        targets,
        "infer_target",
        lambda **kwargs: {
            "kind": "module",
            "name": "network",
            "repo": "Azure/azure-cli",
        },
    )

    assert targets._infer_repository_target(
        text="az network vnet create fails",
        pr_files=[],
    ) == {
        "kind": "module",
        "name": "network",
        "repo": "Azure/azure-cli",
    }
