# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[4]
PIPELINES = ROOT / ".azure-pipelines"
GENERATION = PIPELINES / "templates/standalone/cask-generation-and-tests.yml"


def bash_steps(path):
    lines = path.read_text().splitlines()
    for index, line in enumerate(lines):
        match = re.fullmatch(r"( *)- bash: \|", line)
        if match is None:
            continue
        prefix = " " * (len(match[1]) + 4)
        end = index + 1
        while end < len(lines) and (not lines[end].strip() or lines[end].startswith(prefix)):
            end += 1
        yield textwrap.dedent("\n".join(lines[index + 1:end])), lines[end].strip()


def bash_step(path, display_name):
    return next(script for script, label in bash_steps(path)
                if label == f"displayName: '{display_name}'")


class TestReleasePipeline(unittest.TestCase):

    def run_with_brew_stub(self, script, **settings):
        with tempfile.TemporaryDirectory(prefix="cask commands ") as directory:
            root = Path(directory)
            log = root / "brew.jsonl"
            brew = root / "brew"
            brew.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\n"
                "args = sys.argv[1:]\n"
                "with open(os.environ['BREW_ARGUMENT_LOG'], 'a') as log:\n"
                "    log.write(json.dumps(args) + '\\n')\n"
                "if args == ['list', '--cask', '--full-name']:\n"
                "    print(os.environ.get('INSTALLED_CASKS', ''))\n"
                "if args == ['tap']:\n"
                "    print(os.environ.get('INSTALLED_TAPS', ''))\n"
                "if args and args[0] == os.environ.get('BREW_FAIL_COMMAND'):\n"
                "    sys.exit(7)\n",
            )
            brew.chmod(0o755)
            az = root / "az"
            az.write_text(f"#!{sys.executable}\nprint('2.91.0')\n")
            az.chmod(0o755)
            result = subprocess.run(
                ["/bin/bash", "-c", script.replace("$(Architecture)", "arm64")],
                env={
                    "PATH": str(root) + os.pathsep + os.defpath,
                    "HOME": str(root),
                    "BREW_ARGUMENT_LOG": str(log),
                    **settings,
                },
                cwd=root, capture_output=True, text=True, timeout=10, check=False,
            )
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            return result, calls

    def test_temporary_cleanup_is_specific_and_surfaces_failures(self):
        cleanups = [script for script, label in bash_steps(GENERATION) if label == "displayName: 'Cleanup'"]
        self.assertEqual(len(cleanups), 2)
        installed = {
            "INSTALLED_CASKS": "test/azure-cli-pipeline-test/azure-cli\nhomebrew/cask/another-cask",
            "INSTALLED_TAPS": "test/azure-cli-pipeline-test",
        }
        for script in cleanups:
            with self.subTest(script=script):
                result, calls = self.run_with_brew_stub(script, **installed)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(["uninstall", "--cask", "test/azure-cli-pipeline-test/azure-cli"], calls)
                self.assertIn(["untap", "test/azure-cli-pipeline-test"], calls)
                result, calls = self.run_with_brew_stub(script)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(calls, [["list", "--cask", "--full-name"], ["tap"]])
                for command in ("list", "uninstall", "untap"):
                    result, _ = self.run_with_brew_stub(script, **installed, BREW_FAIL_COMMAND=command)
                    self.assertEqual(result.returncode, 7, result.stderr)

    def test_cask_info_checks_the_installed_temporary_tap(self):
        cask = "test/azure-cli-pipeline-test/azure-cli"
        source = "github.com/test/homebrew-azure-cli-pipeline-test/blob/HEAD/Casks/azure-cli.rb"
        for step in ("Install and test cask", "Install and test Linux cask"):
            with self.subTest(step=step):
                script = bash_step(GENERATION, step)
                self.assertIn(f"brew install --cask {cask}", script)
                info_commands = [line.strip() for line in script.splitlines()
                                 if line.strip().startswith("brew info ")]
                self.assertEqual(info_commands, [
                    f"brew info --cask {cask}",
                    f'brew info --cask {cask} | grep -F "{source}"',
                ])

    def test_string_parameters_never_enter_bash_source(self):
        paths = (
            GENERATION,
            PIPELINES / "templates/macos/macos-build-jobs.yml",
            PIPELINES / "templates/macos/macos-sign-notarize-jobs.yml",
            PIPELINES / "templates/linux/linux-build-jobs.yml",
        )
        count = 0
        for path in paths:
            for script, label in bash_steps(path):
                with self.subTest(path=path, step=label):
                    for field in ("GitHubRepo", "HomebrewTapRepo", "PythonVersion"):
                        self.assertNotIn("${{ parameters." + field + " }}", script)
                    result = subprocess.run(
                        ["bash", "-n"], input=script, capture_output=True, text=True, timeout=10, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                count += 1
        self.assertGreater(count, 15)

    def test_production_pipeline_retains_cask_generation(self):
        text = (ROOT / "azure-pipelines.yml").read_text()
        self.assertIn("template: .azure-pipelines/templates/standalone/cask-generation-and-tests.yml", text)
        generation = GENERATION.read_text()
        self.assertIn("artifactName: 'cask-definition'", generation)

    def test_unchanged_artifact_is_checked_before_staging(self):
        generation = GENERATION.read_text()
        self.assertLess(generation.index("--validate"), generation.index("# Copy to staging"))
        self.assertLess(
            generation.index("displayName: 'Validate unchanged publication cask'"),
            generation.index('url \\"file://$(Pipeline.Workspace)/linux-cli-final'),
        )


if __name__ == "__main__":
    unittest.main()
