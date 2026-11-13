# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import tempfile
import unittest
from unittest import mock

from azure.cli.core.azclierror import FileOperationError, ValidationError
from azure.cli.command_modules.resource._bicep_config import (
    find_bicep_config_file,
    resolve_bicep_version_constraint,
)
from azure.cli.command_modules.resource._bicep_version import parse_bicep_version_constraint


class TestBicepConfig(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=os.path.dirname(__file__))
        self.addCleanup(self.directory.cleanup)
        self.root = self.directory.name

    def write_config(self, relative_path, config):
        path = os.path.join(self.root, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            file.write(config if isinstance(config, str) else json.dumps(config))
        return path

    def test_find_config_from_entrypoint_not_working_directory(self):
        config = self.write_config("bicepconfig.json", {"bicep": {"version": "0.31.92"}})
        for filename in ("main.bicep", "main.bicepparam"):
            with self.subTest(filename=filename):
                entrypoint = os.path.join(self.root, "app", filename)
                self.assertEqual(config, find_bicep_config_file(entrypoint))
                self.assertEqual("0.31.92", resolve_bicep_version_constraint(entrypoint))

    def test_nearest_config_does_not_implicitly_inherit_parent(self):
        self.write_config("bicepconfig.json", {"bicep": {"version": "0.31.92"}})
        config = self.write_config(os.path.join("app", "bicepconfig.json"), {})
        entrypoint = os.path.join(self.root, "app", "main.bicep")
        self.assertEqual(config, find_bicep_config_file(entrypoint))
        self.assertIsNone(resolve_bicep_version_constraint(entrypoint))

    def test_relative_entrypoint_uses_its_own_directory(self):
        self.write_config(os.path.join("app", "bicepconfig.json"), {"bicep": {"version": "0.31.92"}})
        previous_directory = os.getcwd()
        try:
            os.chdir(self.root)
            self.assertEqual("0.31.92", resolve_bicep_version_constraint(os.path.join("app", "main.bicep")))
        finally:
            os.chdir(previous_directory)

    def test_no_config_returns_none(self):
        with mock.patch("azure.cli.command_modules.resource._bicep_config.os.stat", side_effect=FileNotFoundError):
            self.assertIsNone(find_bicep_config_file(os.path.join(self.root, "main.bicep")))
            self.assertIsNone(resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep")))

    def test_extends_paths_are_relative_to_each_declaring_file(self):
        self.write_config(os.path.join("app", "bicepconfig.json"), {"extends": "../shared/base.json"})
        self.write_config(os.path.join("shared", "base.json"), {"extends": "nested/settings.json"})
        self.write_config(os.path.join("shared", "nested", "settings.json"),
                          {"bicep": {"version": ">=0.31.0, <1.0.0"}})
        self.assertEqual(">=0.31.0, <1.0.0",
                         resolve_bicep_version_constraint(os.path.join(self.root, "app", "main.bicepparam")))

    def test_derived_version_overrides_inherited_range(self):
        self.write_config("base.json", {"bicep": {"version": "<0.31.0"}})
        self.write_config("bicepconfig.json", {"extends": "base.json", "bicep": {"version": ">=1.0.0"}})
        self.assertEqual(">=1.0.0", resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep")))

    def test_inherited_constraint_can_be_parsed_and_evaluated(self):
        import semver

        self.write_config("base.json", {"bicep": {"version": ">=0.31, <1"}})
        self.write_config("bicepconfig.json", {"extends": "base.json"})
        raw_constraint = resolve_bicep_version_constraint(os.path.join(self.root, "main.bicepparam"))
        constraint = parse_bicep_version_constraint(raw_constraint)
        self.assertTrue(constraint.is_satisfied_by(semver.VersionInfo.parse("0.31.92")))
        self.assertFalse(constraint.is_satisfied_by(semver.VersionInfo.parse("1.0.0")))

    def test_empty_extends_ends_chain_without_a_constraint(self):
        for extends in (None, "", " \t "):
            with self.subTest(extends=extends):
                self.write_config("bicepconfig.json", {"extends": extends})
                self.assertIsNone(resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep")))

    def test_null_and_missing_values_inherit_but_empty_string_is_preserved(self):
        self.write_config("base.json", {"bicep": {"version": "0.31.92"}})
        for section in (None, {}, {"version": None}, {"other": True}, {"version": ""}):
            with self.subTest(section=section):
                self.write_config("bicepconfig.json", {"extends": "base.json", "bicep": section})
                expected = "" if section == {"version": ""} else "0.31.92"
                self.assertEqual(expected, resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep")))

    def test_json_comments_bom_and_comment_markers_in_strings(self):
        self.write_config("bicepconfig.json", '\ufeff{\n// comment\n"bicep": /* comment */ {"version": "0.31.92"},'
                          '\n"url": "https://example.com/*literal*/", "escaped": "a\\"//b"\n}// eof')
        self.assertEqual("0.31.92", resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep")))

    def test_invalid_json_and_config_shapes_raise(self):
        for config in ('{"bicep":', '{"bicep": {},}', '{} /* unterminated', '{"x": 1/*comment*/2}',
                       '{"x": NaN}', '[]', 'null', '{"bicep": 42}', '{"bicep": {"version": 42}}',
                       '{"extends": []}'):
            with self.subTest(config=config):
                self.write_config("bicepconfig.json", config)
                with self.assertRaisesRegex(ValidationError, "bicepconfig.json"):
                    resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep"))

    def test_invalid_overridden_version_does_not_replace_valid_leaf(self):
        self.write_config("base.json", {"bicep": {"version": 42}})
        self.write_config("bicepconfig.json", {"extends": "base.json", "bicep": {"version": "0.31.92"}})
        self.assertEqual("0.31.92", resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep")))

    def test_missing_base_is_not_ignored_when_leaf_declares_version(self):
        self.write_config("bicepconfig.json", {"extends": "missing.json", "bicep": {"version": "0.31.92"}})
        with self.assertRaisesRegex(FileOperationError, "missing.json"):
            resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep"))

    def test_invalid_base_is_not_ignored_when_leaf_declares_version(self):
        self.write_config("base.json", "{")
        self.write_config("bicepconfig.json", {"extends": "base.json", "bicep": {"version": "0.31.92"}})
        with self.assertRaisesRegex(ValidationError, "base.json"):
            resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep"))

    def test_absolute_and_uri_extends_are_rejected(self):
        for extends in (self.root, "C:\\config.json", "\\\\server\\share\\config.json", "/config.json",
                        "https://example.com/config.json", "file:///config.json"):
            with self.subTest(extends=extends):
                self.write_config("bicepconfig.json", {"extends": extends})
                with self.assertRaisesRegex(ValidationError, "relative file path"):
                    resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep"))

    def test_cycle_is_detected_with_normalized_paths(self):
        self.write_config("bicepconfig.json", {"extends": "base.json", "bicep": {"version": "0.31.92"}})
        self.write_config("base.json", {"extends": "./bicepconfig.json"})
        with self.assertRaisesRegex(ValidationError, "cycle"):
            resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep"))

    def test_chain_depth_boundary_includes_leaf(self):
        self.write_config("bicepconfig.json", {"extends": "base1.json"})
        for index in range(1, 63):
            self.write_config(f"base{index}.json", {"extends": f"base{index + 1}.json"})
        self.write_config("base63.json", {"bicep": {"version": "0.31.92"}})
        entrypoint = os.path.join(self.root, "main.bicep")
        self.assertEqual("0.31.92", resolve_bicep_version_constraint(entrypoint))
        self.write_config("base63.json", {"extends": "base64.json", "bicep": {"version": "0.31.92"}})
        self.write_config("base64.json", {})
        with self.assertRaisesRegex(ValidationError, "64 files"):
            resolve_bicep_version_constraint(entrypoint)

    def test_discovery_permission_error_is_not_treated_as_missing_config(self):
        with mock.patch("azure.cli.command_modules.resource._bicep_config.os.stat", side_effect=PermissionError):
            with self.assertRaises(FileOperationError):
                find_bicep_config_file(os.path.join(self.root, "main.bicep"))

    def test_read_permission_error_is_not_treated_as_no_constraint(self):
        self.write_config("bicepconfig.json", {})
        with mock.patch("azure.cli.command_modules.resource._bicep_config.open", side_effect=PermissionError):
            with self.assertRaises(FileOperationError):
                resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep"))
