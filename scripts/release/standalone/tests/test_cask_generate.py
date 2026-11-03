# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts/release/standalone/cask_generate.py"
TEMPLATE = SCRIPT.parent / "templates/azure-cli.rb.in"
_spec = importlib.util.spec_from_file_location("standalone_cask_generate", SCRIPT)
generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generator)


class TestCaskGenerate(unittest.TestCase):

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="cask validation ")
        self.addCleanup(directory.cleanup)
        self.output = Path(directory.name) / "azure-cli.rb"
        self.values = {
            "version": "2.85.0",
            "arm64_macos_sha": "a" * 64,
            "x86_64_macos_sha": "b" * 64,
            "arm64_linux_sha": "c" * 64,
            "x86_64_linux_sha": "d" * 64,
            "github_repo": "Azure/homebrew-azure-cli",
            "python_version": "3.14",
        }

    def generate(self, **overrides):
        generator.generate_cask(argparse.Namespace(
            **{**self.values, **overrides}, template=str(TEMPLATE), output=str(self.output),
        ))

    def validate(self, **overrides):
        with contextlib.redirect_stdout(io.StringIO()):
            generator.validate_cask(
                self.output, TEMPLATE,
                overrides.get("github_repo", self.values["github_repo"]),
                overrides.get("python_version", self.values["python_version"]),
            )

    def test_valid_output_preserves_existing_template_behavior(self):
        self.generate()
        expected = TEMPLATE.read_text()
        for name, value in self.values.items():
            expected = expected.replace("{{ " + name + " }}", value)
        self.assertEqual(self.output.read_text(), expected)
        self.assertIn("#{version}", expected)
        self.assertIn("#{os}", expected)
        self.assertIn("#{arch}", expected)
        self.validate()

    def test_ci_forks_and_prerelease_versions_remain_supported(self):
        for repo in ("Azure/azure-cli", "test-owner/azure-cli-fork"):
            with self.subTest(repo=repo):
                self.generate(github_repo=repo, version="2.85.0b1")
                self.validate(github_repo=repo)

    def test_rejects_executable_source_in_every_field_without_writing(self):
        for name in self.values:
            for value in ("#{1+1}", "'; printf MARKER; '", '"; printf MARKER; "',
                          "$(printf MARKER)", "\\", "value\nEOF\nprintf MARKER", "", "３.１４"):
                with self.subTest(field=name, value=value):
                    self.output.write_text("unchanged")
                    with self.assertRaises(SystemExit):
                        self.generate(**{name: value})
                    self.assertEqual(self.output.read_text(), "unchanged")

    def test_rejects_embedded_payloads_and_invalid_field_formats(self):
        invalid = {
            "github_repo": (
                "Azure/homebrew-azure-cli#{1+1}", "Azure/repo\n", "Azure/repo\\",
                "https://github.com/Azure/azure-cli", "Azure/repo/extra",
            ),
            "python_version": ("3.14#{1+1}", "3.14\n", "python@3.14", "3.14.0"),
            "version": ("2.85.0#{1+1}", "2.85.0\n", "2.85", "2.85.0\""),
        }
        for name in ("arm64_macos_sha", "x86_64_macos_sha", "arm64_linux_sha", "x86_64_linux_sha"):
            invalid[name] = ("a" * 63, "a" * 65, "g" * 64, "a" * 64 + "\n")
        for name, values in invalid.items():
            for value in values:
                with self.subTest(field=name, value=value):
                    with self.assertRaises(SystemExit):
                        self.generate(**{name: value})
                    self.assertFalse(self.output.exists())

    def test_validation_rejects_tampered_publication_source(self):
        self.generate()
        original = self.output.read_text()
        tampered = (
            original.replace("Azure/homebrew-azure-cli", "Azure/homebrew-azure-cli#{1+1}"),
            original.replace("python@3.14", "python@3.14#{1+1}"),
            original + "\nputs 'unexpected source'\n",
            original.replace('  name "Azure CLI"', '  name "#{1+1}"'),
            original.replace("https://github.com/", "file:///tmp/"),
            original.replace("a" * 64, "invalid-checksum"),
            original.replace("#{arch}", "#{1+1}"),
        )
        for content in tampered:
            with self.subTest(content=content):
                self.output.write_text(content)
                with self.assertRaises(SystemExit):
                    self.validate()

    def test_validation_checks_expected_repository_and_python(self):
        self.generate()
        for settings in ({"github_repo": "other/repo"}, {"python_version": "3.13"},
                         {"github_repo": "Azure/repo#{1+1}"}):
            with self.subTest(settings=settings):
                with self.assertRaises(SystemExit):
                    self.validate(**settings)

    def test_environment_fallbacks_are_validated(self):
        args = argparse.Namespace(**dict.fromkeys(self.values), template=str(TEMPLATE), output=str(self.output))
        with patch.dict(os.environ, {name.upper(): value for name, value in self.values.items()}):
            generator.generate_cask(args)
            self.validate()
            with patch.dict(os.environ, {"GITHUB_REPO": "Azure/repo#{1+1}"}):
                with self.assertRaises(SystemExit):
                    generator.generate_cask(args)

    def test_validation_cli_success_and_failure(self):
        self.generate()
        command = [
            sys.executable, str(SCRIPT), "--validate", str(self.output),
            "--github-repo", self.values["github_repo"], "--python-version", "3.14",
        ]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=10, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated publication cask", result.stdout)
        self.output.write_text(self.output.read_text() + "puts 'unexpected source'\n")
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=10, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match", result.stderr)


if __name__ == "__main__":
    unittest.main()
