# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Pre-publication gates this package's hooks contribute for Azure/azure-cli."""

import base64
import json
from pathlib import Path

import pytest

from x_engineering_agent.repository import testing
from x_engineering_agent.tools.copilot import execution, prepublication

REPOSITORY = "Azure/azure-cli"
PACKAGE = Path(__file__).resolve().parents[1]
TITLE = "[Network] Fix #1: `az network vnet list`: Return all pages"
CLI_MODULE = "src/azure-cli/azure/cli/command_modules/network"
VALIDATION = {"status": "passed", "reports": [{"status": "passed", "lint": {
    "flake8": {"status": "passed"}, "pylint": {"status": "passed"}}}]}


@pytest.fixture(autouse=True)
def pinned(monkeypatch, tmp_path):
    testing.pin(monkeypatch, tmp_path, testing.local(PACKAGE, REPOSITORY))


def _job(title=TITLE, **extra):
    return {"id": "a" * 64, "repository": REPOSITORY, "title": title,
            "base_branch": "dev", "source_kind": "issue", **extra}


def _evaluate(job, base, head, validation=VALIDATION, files=None):
    files = {**head, **(files or {})}
    return prepublication.evaluate_candidate(job, base, head, read_file=files.get, validation=validation)


def _gates(record):
    return {item["gate"] for item in record["findings"]}


def _status(record, gate):
    return next(item["status"] for item in record["checks"] if item["gate"] == gate)


PARAMS_BASE = (
    "def load_arguments(self, _):\n"
    "    with self.argument_context('network vnet list') as c:\n"
    "        c.argument('top', help='Maximum results.')\n"
)
_COMMANDS_BASE = (
    "def load_command_table(self, _):\n    with self.command_group('network vnet') as g:\n"
    "        g.command('list', 'list')\n"
)


@pytest.mark.parametrize(("title", "base", "head"), [
    ("Fix #1: `az network vnet list`: Add zone filter",
     {f"{CLI_MODULE}/_params.py": PARAMS_BASE},
     {f"{CLI_MODULE}/_params.py": PARAMS_BASE + "        c.argument('zone', help='Zone to filter by.')\n"}),
    (TITLE, {"src/azure-cli/HISTORY.rst": "Release\n"}, {"src/azure-cli/HISTORY.rst": "Release\n* fix\n"}),
], ids=["param-needs-note", "history-edit"])
def test_release_artifact_gate(title, base, head):
    record = _evaluate(_job(title), base, head)
    assert _status(record, "release-artifact") == "blocked" and record["status"] == "blocked"


def test_aaz_regeneration_is_not_blocked_downstream():
    path = f"{CLI_MODULE}/aaz/latest/network/vnet/_list.py"
    record = _evaluate(_job(), {path: "x = 1\n"}, {path: "x = 2\n"})
    assert "generated-ownership" not in _gates(record)


@pytest.mark.parametrize(("path", "base", "head", "files"), [
    (f"{CLI_MODULE}/_help.py",
     "helps['network vnet list'] = \"\"\"\ntype: command\nshort-summary: List.\n\"\"\"\n",
     "helps['network vnet list'] = \"\"\"\ntype: command\n"
     "examples:\n  - name: List\n    text: network vnet list\n\"\"\"\n", None),
    (f"{CLI_MODULE}/commands.py", _COMMANDS_BASE,
     _COMMANDS_BASE + "        g.custom_command('repair', 'repair_vnet')\n",
     {f"{CLI_MODULE}/_help.py": "helps['network vnet list'] = 'type: command'\n"}),
    (f"{CLI_MODULE}/_params.py", PARAMS_BASE,
     PARAMS_BASE + "        c.argument('zone', options_list=['--zone'])\n", None),
], ids=["help-without-summary", "command-without-help", "param-without-help"])
def test_missing_command_help_is_blocked(path, base, head, files):
    record = _evaluate(_job(), {path: base}, {path: head}, files=files)
    assert "command-help" in _gates(record)


def test_scenario_coverage_gate():
    path = f"{CLI_MODULE}/custom.py"
    test = f"{CLI_MODULE}/tests/latest/test_network.py"
    validation = {**VALIDATION, "needs_test_evidence": True}

    blocked = _evaluate(_job(), {path: "x = 1\n"}, {path: "x = 2\n"}, validation=validation)
    unknown = _evaluate(_job(), {path: "x = 1\n"}, {path: "x = 2\n"}, validation={"status": "passed"})
    covered = _evaluate(_job(), {path: "x = 1\n", test: None},
                        {path: "x = 2\n", test: "def test_x():\n    pass\n"}, validation=validation)

    assert "scenario-coverage" in _gates(blocked)
    assert _status(unknown, "scenario-coverage").startswith("not run")
    assert _status(covered, "scenario-coverage") == "passed"


_ARTIFACT = {"files": [{"path": f"{CLI_MODULE}/custom.py"}]}
_BODY = (
    "**Related command**\n`az network vnet list`\n\n**Description**\n"
    "Fixes #1. <br> `<x>`\n\n**Testing Guide**\n- Unit tests passed.\n\n"
    "**History Notes**\nGenerated from the pull request title.\n\n---\n\n"
    "- [ ] The PR title and description has followed the guideline.\n"
    "- [ ] I adhere to the [Command Guidelines](https://example.test).\n"
    "- [ ] I adhere to the [Error Handling Guidelines](https://example.test).\n"
)


def test_title_without_component_is_blocked():
    record = prepublication.evaluate_metadata(_job("Fix vnet list paging"))
    assert any(item["gate"] == "pr-title" for item in record["findings"])


def test_title_component_must_match_changed_module():
    job = _job("[Compute] Fix #1: `az network vnet list`: Return all pages", artifact=_ARTIFACT)
    record = prepublication.evaluate_metadata(job)
    assert any("Network" in item["summary"] for item in record["findings"])


def test_valid_cli_metadata_passes():
    record = prepublication.evaluate_metadata(_job(artifact=_ARTIFACT), body=_BODY)
    assert record["status"] == "passed", record["findings"]


def test_candidate_gates_read_validated_tree_and_base_snapshot(tmp_path):
    path = f"{CLI_MODULE}/_params.py"
    head = PARAMS_BASE + "        c.argument('zone')\n"
    work = tmp_path / "work"
    (work / CLI_MODULE).mkdir(parents=True)
    (work / path).write_text(head)
    files = [{"path": path, "mode": "100644", "content": base64.b64encode(head.encode()).decode()}]
    snapshot = json.dumps({"files": {path: base64.b64encode(PARAMS_BASE.encode()).decode()}})

    record = execution._prepublication_gates(_job(), work, files, snapshot)
    unknown_base = execution._prepublication_gates(_job(), work, files, None)

    assert "command-help" in _gates(record)
    assert _status(unknown_base, "command-help") == "not run: base revision unavailable"


AAZ_FILE = f"{CLI_MODULE}/aaz/latest/network/vnet/_show.py"
AAZ_NEW = f"{CLI_MODULE}/aaz/latest/network/vnet/_new.py"
AAZ_HEADER = "# Code generated by aaz-dev-tools\n# pylint: skip-file\n"
AZAPI = "Azure/terraform-provider-azapi"
AZAPI_AAZ = "internal/aaz/latest/thing/_show.py"
AZAPI_PACKAGE = """schema_version: 1
repository: Azure/terraform-provider-azapi
profile:
  base_branch: main
  kind: terraform-provider
  module_root: internal
  target_kind: provider
  workflow: analysis-only
  triage_agent: tf_requirements
  live_test: false
"""


def _ownership(repository, base, head, **job):
    changes = prepublication.changes_from_contents(base, head)
    return prepublication.generated_ownership_gate(
        repository, {**_job(), "repository": repository, **job}, changes, base, head)


@pytest.mark.parametrize(("base", "head", "status", "problem"), [
    ({AAZ_FILE: AAZ_HEADER + "x = 1\n"}, {AAZ_FILE: AAZ_HEADER + "x = 2\n"}, "passed", None),
    ({AAZ_FILE: AAZ_HEADER + "x = 1\n"}, {AAZ_FILE: "x = 2\n"}, "blocked", "aaz-dev"),
    ({AAZ_NEW: None}, {AAZ_NEW: "x = 1\n"}, "blocked", None),
], ids=["aaz-regenerated", "aaz-hand-edit", "aaz-new-file"])
def test_generated_ownership_gate(base, head, status, problem):
    result, findings = _ownership(REPOSITORY, base, head)

    assert result == status
    if status == "passed":
        assert findings == []
    if problem:
        assert any(problem in item["summary"] or problem in item["remediation"] for item in findings), findings


@pytest.mark.parametrize(("job", "status"), [
    ({}, "blocked"),
    ({"generation_source_pr_url": "https://github.com/Azure/aaz/pull/7"}, "passed"),
], ids=["azapi-aaz-unpaired", "azapi-aaz-paired"])
def test_aaz_output_in_another_repository_needs_a_command_model_change(monkeypatch, tmp_path, job, status):
    azapi = testing.read_sources(AZAPI, testing.TEST_REVISION, {
        "x.yml": AZAPI_PACKAGE, "definitions/coordinator.md": "Route work.\n",
        "definitions/tf_requirements.md": "Triage issues.\n"})
    testing.pin(monkeypatch, tmp_path, testing.local(PACKAGE, REPOSITORY), azapi)

    result, findings = _ownership(
        AZAPI, {AZAPI_AAZ: AAZ_HEADER + "x = 1\n"}, {AZAPI_AAZ: AAZ_HEADER + "x = 2\n"}, **job)

    assert result == status
    if status == "blocked":
        assert any("Azure/aaz command-model" in item["summary"] + item["remediation"] for item in findings), findings
    else:
        assert findings == []
