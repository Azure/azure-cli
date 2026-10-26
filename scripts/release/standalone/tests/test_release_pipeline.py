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
PUBLISH = PIPELINES / "templates/standalone/publish-jobs.yml"
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

    def test_string_parameters_never_enter_bash_source(self):
        paths = (
            PUBLISH, GENERATION,
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
        self.assertGreater(count, 20)

    def test_no_free_form_queue_parameters_or_repository_macros(self):
        text = (PIPELINES / "mac-and-linux-standalone-release.yml").read_text()
        parameters = text.split("\nparameters:\n", 1)[1].split("\nresources:", 1)[0]
        self.assertEqual(parameters.count("type: boolean"), 3)
        self.assertNotIn("type: string", parameters)
        for field in ("GitHubRepo", "HomebrewTapRepo", "PythonVersion", "BundleId", "ESRPServiceConnection"):
            self.assertNotIn("${{ parameters." + field + " }}", text)
            self.assertNotIn("$(" + field + ")", text)

    def test_python_version_is_defined_once_and_shared_at_template_expansion(self):
        text = (PIPELINES / "mac-and-linux-standalone-release.yml").read_text()
        self.assertRegex(
            text,
            r"- name: standalone_python_version\n    value: '3\.[0-9]+'\n    readonly: true",
        )
        self.assertEqual(text.count("- name: standalone_python_version"), 1)
        self.assertEqual(text.count("PythonVersion:"), 5)
        self.assertEqual(text.count("PythonVersion: ${{ variables.standalone_python_version }}"), 5)
        self.assertNotIn("$(standalone_python_version)", text)

    def test_unchanged_artifact_is_checked_before_staging_and_publication(self):
        generation = GENERATION.read_text()
        self.assertLess(generation.index("--validate"), generation.index("# Copy to staging"))
        self.assertLess(
            generation.index("displayName: 'Validate unchanged publication cask'"),
            generation.index('url \\"file://$(Pipeline.Workspace)/linux-cli-final'),
        )
        publication = PUBLISH.read_text().split("- job: UpdateHomebrewCask", 1)[1]
        self.assertLess(publication.index("--validate"), publication.index("- checkout: homebrewtap"))
        self.assertIn('cmp "$(Pipeline.Workspace)/cask-definition/azure-cli.rb"', publication)
        gate = bash_step(PUBLISH, "Validate unchanged publication cask before tap checkout")
        self.assertNotIn("PublishToGitHub", gate)
        self.assertNotIn("GH_TOKEN", gate)

    def test_release_input_stays_data_even_with_shell_and_heredoc_metacharacters(self):
        with tempfile.TemporaryDirectory(prefix="release data ") as directory:
            root = Path(directory)
            tools = root / "tools"
            tools.mkdir()
            log = root / "gh.jsonl"
            gh = tools / "gh"
            gh.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\n"
                "with open(os.environ['GH_ARGUMENT_LOG'], 'a') as log:\n"
                "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n",
            )
            gh.chmod(0o755)
            (root / "azure-cli-test.tar.gz").write_text("fixture")
            repository = "Azure/repo'; printf INJECTION_EXECUTED; #"
            tap = "Azure/tap\nEOF\nprintf INJECTION_EXECUTED\n"
            python_version = "3.14$(printf INJECTION_EXECUTED)"
            environment = {
                **os.environ,
                "PATH": str(tools),
                "GH_ARGUMENT_LOG": str(log),
                "RELEASE_TAG": "azure-cli-2.85.0",
                "RELEASE_VERSION": "2.85.0",
                "RELEASE_TEMP_DIRECTORY": str(root),
                "RELEASE_DIRECTORY": str(root),
                "RELEASE_GITHUB_REPO": repository,
                "RELEASE_HOMEBREW_TAP": tap,
                "RELEASE_PYTHON_VERSION": python_version,
            }
            environment.pop("GH_TOKEN", None)
            result = subprocess.run(
                ["/bin/bash", "-c", bash_step(PUBLISH, "Create GitHub Release with PAT")],
                env=environment, capture_output=True, text=True, timeout=10, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(len(calls), 2)
            for call in calls:
                self.assertEqual(call[call.index("--repo") + 1], repository)
            notes = (root / "release-notes.md").read_text()
            self.assertIn("brew tap " + tap, notes)
            self.assertIn("Homebrew Python " + python_version, notes)


if __name__ == "__main__":
    unittest.main()
