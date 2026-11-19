# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""The engine's SWE replay harness builds azure-cli environments from this package."""

from pathlib import Path

import pytest

from x_engineering_agent.release_evaluation.swe_replay.dataset import ReplayCase
from x_engineering_agent.release_evaluation.swe_replay.harness import (
    GitCheckoutHarness, repository_environment,
)
from x_engineering_agent.repository import testing

REPOSITORY = "Azure/azure-cli"
PACKAGE = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def pinned(monkeypatch, tmp_path):
    testing.pin(monkeypatch, tmp_path, testing.local(PACKAGE, REPOSITORY))


def case(framework="pytest"):
    return ReplayCase(
        id="c", repository=REPOSITORY, issue_number=1, base_sha="0" * 40, issue={},
        test_framework=framework,
        fail_to_pass=("src/azure-cli/azure/cli/command_modules/vm/tests/test_vm.py::test_a",),
    )


def test_editable_checkout_packages_in_case_venv(tmp_path):
    environment = repository_environment(case(), Path("/work/c/repo"), "/usr/bin/python3")
    assert environment.python == "/work/c/venv/bin/python"
    assert environment.commands[0] == ["/usr/bin/python3", "-m", "venv", "/work/c/venv"]
    assert environment.commands[-1][-4:] == [
        "--editable=src/azure-cli-telemetry", "--editable=src/azure-cli-core",
        "--editable=src/azure-cli", "--editable=src/azure-cli-testsdk",
    ]
    assert environment.env == {"AZURE_CORE_COLLECT_TELEMETRY": "false"}


def test_default_harness_uses_package_environment(tmp_path):
    harness = GitCheckoutHarness(tmp_path, python="/usr/bin/python3")
    assert harness.environment(case(), tmp_path / "c" / "repo").python == str(tmp_path / "c" / "venv" / "bin" / "python")


def test_non_pytest_cases_have_no_environment():
    assert repository_environment(case("go"), Path("/work/c/repo"), "python") is None
