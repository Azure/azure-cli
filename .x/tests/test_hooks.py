# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Run this package's engine hooks through the X Engineering Agent broker."""

from pathlib import Path

import pytest

from x_engineering_agent.repository import testing

REPOSITORY = "Azure/azure-cli"
PACKAGE = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def pinned(monkeypatch, tmp_path):
    testing.pin(monkeypatch, tmp_path, testing.local(PACKAGE, REPOSITORY))


DIRECTORIES = {
    ("Azure", "azure-cli", "src/azure-cli/azure/cli/command_modules"): {"vm", "network", "storage"},
    ("Azure", "azure-cli-extensions", "src"): {"containerapp", "aks-preview"},
}


@pytest.fixture(autouse=True)
def offline_directories(monkeypatch):
    from x_engineering_agent.tools.targets import discovery

    def listing(owner, repo, path, branch, token=None):
        return set(DIRECTORIES[(owner, repo, path)])

    monkeypatch.setattr(discovery, "_list_repo_dirs", listing)


def hook(name, *args, **kwargs):
    return testing.hook(REPOSITORY, name, *args, **kwargs)


def test_targets_follow_command_module_layout():
    target = hook("infer_target", "az vm create fails", ["src/azure-cli/azure/cli/command_modules/vm/custom.py"])
    assert target["name"] == "vm"
    assert hook("resolve_target", "vm")["name"] == "vm"


def test_titles_use_cli_style():
    title = hook("pr_title", component="vm", issue_number=1, command="az vm create", summary="Fix up")
    assert title.startswith("[")
    assert "vm" in title.lower()
    assert hook("pr_format_guidance", component="vm", issue_number=1)
    assert hook("execution_instructions")


def test_codegen_guidance_targets_core():
    assert isinstance(hook("codegen_guidance", "vm"), str)


def test_changed_tests_and_failures():
    files = ["src/azure-cli/azure/cli/command_modules/vm/tests/latest/test_vm_commands.py"]
    assert hook("changed_test_files", files)
    failed = hook("extract_failed_tests", "FAILED src/x/tests/latest/test_a.py::Test::test_b - boom")
    assert failed


def test_readiness_requires_validation_and_a_matching_title():
    pr = {"title": "[Compute] `az vm create`: Fix", "body": "",
          "head": {"sha": "a" * 40, "repo": {"full_name": "fork/azure-cli"}}}
    changes = [{"filename": "src/azure-cli/azure/cli/command_modules/vm/custom.py", "status": "modified"}]
    policy = hook("readiness_policy", pr, changes)
    assert policy["validation_required"] is True


def test_definitions_reference_existing_engine_helpers_and_tools():
    assert testing.definition_problems(testing.local(PACKAGE, REPOSITORY)) == []
