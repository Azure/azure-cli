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
    _load_bicep_config,
    _strip_json_comments,
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

    def test_comment_scanner_preserves_strings_and_handles_comment_variants(self):
        expected = {
            "bicep": {"version": "0.31.92"},
            "strings": ['https://example.com/*literal*/', 'a"//b', '\\', '\\"/*literal*/', '/*!literal*/'],
        }
        config = json.dumps(expected)
        for newline in ("\n", "\r", "\r\n"):
            with self.subTest(newline=newline):
                contents = (
                    "/* leading */" + newline + "// line comment" + newline +
                    config.replace('"bicep":', '"bicep": /*! inline */ /** adjacent */') +
                    newline + "/* multiline" + newline + "comment */ // eof"
                )
                path = self.write_config("bicepconfig.json", contents)
                self.assertEqual(expected, _load_bicep_config(path))

    def test_comment_scanner_preserves_positions_and_token_boundaries(self):
        contents = '{/*x\r\ny*/"x": 1/*gap*/2}// eof'
        expected = '{   \r\n   "x": 1       2}      '
        self.assertEqual(expected, _strip_json_comments(contents))
        with self.assertRaises(json.JSONDecodeError) as error:
            json.loads(_strip_json_comments(contents))
        self.assertEqual(contents.index("2"), error.exception.pos)

    def test_unterminated_block_comments_report_config_path(self):
        for comment in ("/*", "/**", "/*! notice", "/* unterminated *", "/* // not a line comment"):
            with self.subTest(comment=comment):
                self.write_config("bicepconfig.json", '{"bicep": {"version": "0.31.92"}}' + comment)
                with self.assertRaisesRegex(ValidationError, "bicepconfig.json.*Unterminated block comment"):
                    resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep"))

    def test_empty_adjacent_and_mixed_comments(self):
        for contents in (
                '/**//**/{"bicep"/**/:/**/{"version"/**/:/**/"0.31.92"/**/}/**/}/**/',
                '// " /* not a block comment\n{"bicep": {"version": "0.31.92"}}// /*',
                '/* " // /* not nested */{"bicep": {"version": "0.31.92"}}',
                '{"bicep": {"version": "0.31.92"}, "values": [/*first*/1,/**/2/*last*/]}'):
            with self.subTest(contents=contents):
                self.write_config("bicepconfig.json", contents)
                self.assertEqual("0.31.92",
                                 resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep")))

    def test_backslash_sequences_do_not_change_string_or_comment_boundaries(self):
        for count in range(6):
            with self.subTest(backslashes=count):
                expected = {
                    "bicep": {"version": "0.31.92"},
                    "escaped": "\\" * count + '"//literal/*literal*/',
                    "ending": "text" + "\\" * count,
                }
                contents = json.dumps(expected)[:-1] + '/* actual comment */}// eof'
                path = self.write_config("bicepconfig.json", contents)
                self.assertEqual(expected, _load_bicep_config(path))

    def test_comments_are_parsed_in_each_inheritance_layer(self):
        self.write_config("bicepconfig.json",
                          '{"extends": /* base path */ "shared/base.json" /* leaf */}')
        self.write_config(os.path.join("shared", "base.json"),
                          '// base\n{"extends": "version.json", "bicep": {"version": null}}')
        self.write_config(os.path.join("shared", "version.json"),
                          '/*! inherited settings */{"bicep": {"version": ">=0.31, <1"}}// eof')
        self.assertEqual(">=0.31, <1",
                         resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep")))
        self.write_config(os.path.join("shared", "version.json"), '{"bicep": {}} /* unfinished')
        with self.assertRaisesRegex(ValidationError, r"version.json.*Unterminated block comment"):
            resolve_bicep_version_constraint(os.path.join(self.root, "main.bicep"))

    def test_comment_removal_does_not_make_invalid_json_valid(self):
        for contents in (
                '{"x": -/*gap*/1}', '{"x": 1/*gap*/.5}', '{"x": 1e/*gap*/2}',
                '{"x": tr/*gap*/ue}', '{"x": nu/*gap*/ll}', '{"bi/*gap*/cep": 1,}',
                '{"x": [1,/*gap*/]}', '{"x": 1,/*gap*/}', '{"x": "a"/*gap*/"b"}',
                '{"x": 1}/', '{"x": 1}/*closed*/ */', '// only a comment', '/* only a comment */',
                '{"x": "unfinished' + "\\"):
            with self.subTest(contents=contents):
                path = self.write_config("bicepconfig.json", contents)
                with self.assertRaisesRegex(ValidationError, "Unable to parse Bicep configuration"):
                    _load_bicep_config(path)

    def test_unterminated_strings_are_left_for_json_validation(self):
        for contents in ('{"x": "unfinished // literal', '{"x": "unfinished /* literal',
                         '{"x": "escaped quote \\" // literal'):
            with self.subTest(contents=contents):
                self.assertEqual(contents, _strip_json_comments(contents))
                path = self.write_config("bicepconfig.json", contents)
                with self.assertRaisesRegex(ValidationError, "Unterminated string"):
                    _load_bicep_config(path)

    def test_invalid_json_and_config_shapes_raise(self):
        for config in ('{"bicep":', '{"bicep": {},}', '{} /* unterminated', '{"x": 1/*comment*/2}',
                       '{"x": NaN}', '{"x": Infinity}', '{"x": -Infinity}', "{'x': 1}", '{x: 1}',
                       '{"x": "unterminated // text}', '{"x": "unterminated /* text}',
                       '{"x": "literal\nnewline"}', '[]', 'null', '{"bicep": 42}', '{"bicep": {"version": 42}}',
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
