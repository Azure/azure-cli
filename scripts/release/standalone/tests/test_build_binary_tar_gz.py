# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts/release/standalone/build_binary_tar_gz.py"
_spec = importlib.util.spec_from_file_location("standalone_tarball_builder", SCRIPT)
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)


class TestBuildPlatforms(unittest.TestCase):

    def test_supported_tags_preserve_both_linux_architectures(self):
        self.assertEqual(set(builder.PLATFORM_TAGS), {"macos-arm64", "linux-arm64", "linux-x86_64"})
        for tag, machines in (
            ("macos-arm64", ("arm64", "aarch64")),
            ("linux-arm64", ("arm64", "aarch64")),
            ("linux-x86_64", ("x86_64", "AMD64", "x64")),
        ):
            for machine in machines:
                with self.subTest(tag=tag, machine=machine), patch.object(builder.platform, "machine", return_value=machine):
                    builder._validate_build_architecture(tag)

    def test_retired_tag_fails_before_build_tools_or_output(self):
        with patch.object(sys, "argv", [str(SCRIPT), "--platform-tag", "macos-x86_64"]), \
                patch.object(builder, "find_homebrew_python") as find_python, \
                patch.object(builder, "get_cli_version") as get_version, \
                patch.object(builder.tempfile, "TemporaryDirectory") as temporary_directory, \
                patch.object(builder, "create_tarball") as create_tarball, \
                contextlib.redirect_stderr(io.StringIO()) as errors, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 1)
        self.assertIn("Intel macOS (macos-x86_64) is retired", errors.getvalue())
        self.assertIn("cryptography 49+", errors.getvalue())
        find_python.assert_not_called()
        get_version.assert_not_called()
        temporary_directory.assert_not_called()
        create_tarball.assert_not_called()

    def test_architecture_mismatch_still_fails(self):
        with patch.object(builder.platform, "machine", return_value="x86_64"):
            with self.assertRaisesRegex(builder.BuildError, "requires arm64"):
                builder._validate_build_architecture("macos-arm64")

    def test_unknown_platform_fails_clearly(self):
        with self.assertRaisesRegex(builder.BuildError, "Unsupported platform tag"):
            builder._validate_build_architecture("unsupported")

    def test_cli_rejects_retired_platform(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--platform-tag", "macos-x86_64"],
            cwd=ROOT, capture_output=True, text=True, timeout=10, check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Intel macOS (macos-x86_64) is retired", result.stderr)

    def test_cli_help_lists_only_supported_tags(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=ROOT, capture_output=True, text=True, timeout=10, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("macos-x86_64", result.stdout)
        for tag in builder.PLATFORM_TAGS:
            self.assertIn(tag, result.stdout)


if __name__ == "__main__":
    unittest.main()
