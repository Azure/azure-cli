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
module = sys.modules.get("repository_tools")
if module is None:
    module = types.ModuleType("repository_tools")
    module.__path__ = [str(TOOLS)]
    sys.modules["repository_tools"] = module
elif str(TOOLS) not in module.__path__:
    module.__path__.append(str(TOOLS))

checks = importlib.import_module("repository_tools.validation.checks")


def _unit_test(path, class_name):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "import unittest\n\n"
        f"class {class_name}(unittest.TestCase):\n"
        "    pass\n",
        encoding="utf-8",
    )
    return path


def test_azure_cli_validation_selects_changed_and_matching_tests(tmp_path):
    module = tmp_path / "src/azure-cli/azure/cli/command_modules/acs"
    source = module / "custom.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    matching = _unit_test(module / "tests/latest/test_custom.py", "CustomTests")
    _unit_test(module / "tests/latest/test_unrelated.py", "UnrelatedTests")

    assert checks.python_unit_files("Azure/azure-cli", tmp_path, [source, matching]) == [matching]


def test_validation_keeps_test_names_bound_to_their_component(tmp_path):
    acs = tmp_path / "src/azure-cli/azure/cli/command_modules/acs"
    custom = acs / "custom.py"
    custom.parent.mkdir(parents=True)
    custom.write_text("VALUE = 1\n", encoding="utf-8")
    acs_test = _unit_test(acs / "tests/latest/test_custom.py", "CustomTests")
    _unit_test(acs / "tests/latest/test_validators.py", "UnrelatedValidatorTests")
    core = tmp_path / "src/azure-cli-core/azure/cli/core/commands"
    validators = core / "validators.py"
    validators.parent.mkdir(parents=True)
    validators.write_text("VALUE = 1\n", encoding="utf-8")
    core_test = _unit_test(tmp_path / "src/azure-cli-core/tests/test_validators.py", "CoreValidatorTests")

    selected = checks.python_unit_files("Azure/azure-cli", tmp_path, [custom, validators])

    assert set(selected) == {core_test, acs_test}


def test_validation_normalizes_private_module_test_name(tmp_path):
    module = tmp_path / "src/azure-cli/azure/cli/command_modules/acs"
    source = module / "_validators.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    matching = _unit_test(module / "tests/latest/test_validators.py", "ValidatorTests")

    assert checks.python_unit_files("Azure/azure-cli", tmp_path, [source]) == [matching]


def test_validation_selects_nearest_component_for_duplicate_test_names(tmp_path):
    core = tmp_path / "src/azure-cli-core/azure/cli/core"
    source = core / "util.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    matching = _unit_test(core / "tests/test_util.py", "CoreUtilTests")
    _unit_test(core / "auth/tests/test_util.py", "AuthUtilTests")

    assert checks.python_unit_files("Azure/azure-cli", tmp_path, [source]) == [matching]
