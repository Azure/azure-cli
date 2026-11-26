# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Keep security minimums and development platform checks aligned."""

from pathlib import Path
import unittest

import yaml
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from automation.utilities.packaging import tomllib


ROOT = Path(__file__).resolve().parents[3]
MINIMUMS = {
    'cryptography': '50.0.2',
    'pyopenssl': '26.4.0',
    'urllib3': '2.8.0',
}
RUNTIME_PACKAGES = {
    'cryptography': 'azure-cli-core',
    'pyopenssl': 'azure-cli-core',
    'urllib3': 'azure-cli',
}


class DependencyPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.platforms = {}
        for platform in ('windows', 'Linux', 'Darwin'):
            path = ROOT / 'src' / 'azure-cli' / ('requirements.py3.' + platform + '.txt')
            cls.platforms[platform] = {
                canonicalize_name(requirement.name): requirement
                for line in path.read_text(encoding='utf-8').splitlines()
                if line.strip() and not line.lstrip().startswith('#')
                for requirement in [Requirement(line)]
            }
        cls.runtime = {}
        for package in ('azure-cli', 'azure-cli-core'):
            with (ROOT / 'src' / package / 'pyproject.toml').open('rb') as stream:
                dependencies = tomllib.load(stream)['project']['dependencies']
            cls.runtime[package] = {
                canonicalize_name(requirement.name): requirement
                for dependency in dependencies
                for requirement in [Requirement(dependency)]
            }

    def test_platform_pins_share_security_minimums(self):
        for name, minimum in MINIMUMS.items():
            versions = set()
            for platform, requirements in self.platforms.items():
                with self.subTest(package=name, platform=platform):
                    specifiers = list(requirements[name].specifier)
                    self.assertEqual(len(specifiers), 1)
                    self.assertEqual(specifiers[0].operator, '==')
                    self.assertGreaterEqual(Version(specifiers[0].version), Version(minimum))
                    versions.add(specifiers[0].version)
            self.assertEqual(len(versions), 1, name)

    def test_pip_metadata_enforces_security_minimums(self):
        for name, minimum in MINIMUMS.items():
            with self.subTest(package=name):
                requirement = self.runtime[RUNTIME_PACKAGES[name]][name]
                self.assertTrue(any(
                    specifier.operator == '>='
                    and Version(specifier.version) >= Version(minimum)
                    for specifier in requirement.specifier
                ), f'{requirement} must enforce a minimum of {minimum} or newer')

    def test_shipped_versions_satisfy_runtime_metadata(self):
        for platform, requirements in self.platforms.items():
            for name in MINIMUMS:
                with self.subTest(package=name, platform=platform):
                    version = next(iter(requirements[name].specifier)).version
                    self.assertIn(version, self.runtime[RUNTIME_PACKAGES[name]][name].specifier)


class DevelopmentPlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pipeline = yaml.safe_load((ROOT / 'azure-pipelines.yml').read_text(encoding='utf-8'))
        cls.jobs = {job['job']: job for job in pipeline['jobs'] if 'job' in job}

    def test_windows_build_and_installation_matrices_are_x64_only(self):
        for name in ('BuildWindowsMSI', 'TestMsiInstallation',
                     'BuildWindowsZIP', 'TestZipInstallation'):
            with self.subTest(job=name):
                matrix = self.jobs[name]['strategy']['matrix']
                self.assertEqual(matrix, {'x64': {'Platform': 'x64'}})
        self.assertEqual(self.jobs['TestMsiInstallation']['dependsOn'], 'BuildWindowsMSI')
        self.assertEqual(self.jobs['TestZipInstallation']['dependsOn'], 'BuildWindowsZIP')

    def test_darwin_requirements_use_native_arm64_python(self):
        variables = yaml.safe_load(
            (ROOT / '.azure-pipelines' / 'templates' / 'variables.yml').read_text(encoding='utf-8')
        )['variables']
        self.assertEqual(variables['macos_pool'], variables['macos_arm64_pool'])
        self.assertNotIn('macos_intel_pool', variables)
        job = self.jobs['VerifyDarwinRequirements']
        self.assertEqual(job['pool']['vmImage'], '${{ variables.macos_pool }}')
        python_step = next(step for step in job['steps'] if step.get('task') == 'UsePythonVersion@0')
        self.assertEqual(python_step['inputs']['architecture'], 'arm64')


if __name__ == '__main__':
    unittest.main()
