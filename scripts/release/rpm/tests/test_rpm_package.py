# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    'rpm_package', Path(__file__).resolve().parents[1] / 'test_rpm_package.py')
rpm_package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rpm_package)


class FedoraBuildConfigurationTests(unittest.TestCase):
    def test_native_python_defaults_and_override(self):
        dockerfile = (Path(__file__).resolve().parents[1] / 'fedora.dockerfile').read_text(encoding='utf-8')
        self.assertIn('ARG image=registry.fedoraproject.org/fedora:44\n', dockerfile)
        self.assertIn('ARG python_package=python3\n', dockerfile)
        self.assertIn('ARG python_cmd=${python_package}\n', dockerfile)
        self.assertIn('PYTHON_PACKAGE=$python_package PYTHON_CMD=$python_cmd', dockerfile)

    def test_both_installation_smoke_checks(self):
        dockerfile = (Path(__file__).resolve().parents[1] / 'fedora.dockerfile').read_text(encoding='utf-8')
        execution_stage = dockerfile.split('AS execution-env', 1)[1]
        self.assertIn('dnf install -y ./azure-cli-dev.rpm', execution_stage)
        self.assertIn('az --version &&', execution_stage)
        self.assertIn('az self-test', execution_stage)


class VerifyRpmInstallationTests(unittest.TestCase):
    def setUp(self):
        self.metadata = 'azure-cli 2.90.0 1.fc44 x86_64'
        self.arch = 'x86_64'
        self.version = '2.90.0'
        self.requires = '/usr/bin/bash\npython3\n'
        output_patch = patch.object(rpm_package.subprocess, 'check_output', side_effect=self.command_output)
        call_patch = patch.object(rpm_package.subprocess, 'check_call')
        self.output = output_patch.start()
        self.call = call_patch.start()
        self.addCleanup(output_patch.stop)
        self.addCleanup(call_patch.stop)

    def command_output(self, command, *, text):
        self.assertTrue(text)
        if command[:3] == ['rpm', '-q', '--queryformat']:
            return self.metadata
        if command == ['rpm', '--eval', '%{_arch}']:
            return self.arch
        if command == ['az', 'version', '--query', '"azure-cli"', '--output', 'tsv']:
            return self.version
        if command == ['rpm', '-q', '--requires', 'azure-cli']:
            return self.requires
        self.fail(f'Unexpected command: {command}')

    def test_native_artifact_and_python_dependency(self):
        for distro, python_package in [('fc44', 'python3'), ('el8', 'python3.12'),
                                       ('el9', 'python3.12'), ('el10', 'python3.12')]:
            for arch in ['x86_64', 'aarch64']:
                with self.subTest(distro=distro, arch=arch):
                    self.metadata = f'azure-cli 2.90.0 1.{distro} {arch}'
                    self.arch = arch
                    self.requires = f'/usr/bin/bash\n{python_package}\n'
                    rpm_package.verify_rpm_installation(f'azure-cli-2.90.0-1.{distro}.*.rpm', python_package)
                    self.call.assert_called_with(['rpm', '-q', python_package])

    def test_azure_linux_version_only_artifact_pattern(self):
        for distro in ['azl3', 'azl4']:
            for arch in ['x86_64', 'aarch64']:
                with self.subTest(distro=distro, arch=arch):
                    self.metadata = f'azure-cli 2.90.0 1.{distro} {arch}'
                    self.arch = arch
                    rpm_package.verify_rpm_installation('azure-cli-2.90.0*.rpm')
        self.call.assert_not_called()

    def test_existing_caller_without_optional_environment(self):
        for version in ['2.90.0', 'dev']:
            with self.subTest(version=version):
                self.metadata = f'azure-cli {version} 1.fc44 x86_64'
                rpm_package.verify_rpm_installation()
        self.call.assert_not_called()

    def test_default_development_rpm_label(self):
        for distro, python_package in [('fc44', 'python3'), ('el8', 'python3.12'),
                                       ('el9', 'python3.12'), ('el10', 'python3.12'),
                                       ('azl3', None), ('azl4', None)]:
            for arch in ['x86_64', 'aarch64']:
                with self.subTest(distro=distro, arch=arch):
                    self.metadata = f'azure-cli dev 1.{distro} {arch}'
                    self.arch = arch
                    self.requires = f'/usr/bin/bash\n{python_package or "python3"}\n'
                    self.call.reset_mock()
                    pattern = f'azure-cli-dev-1.{distro}.*.rpm' if python_package else 'azure-cli-dev*.rpm'
                    rpm_package.verify_rpm_installation(pattern, python_package)
                    if python_package:
                        self.call.assert_called_once_with(['rpm', '-q', python_package])
                    else:
                        self.call.assert_not_called()

    def test_wrong_distribution_or_requested_version(self):
        for pattern in ['azure-cli-2.90.0-1.el9.*.rpm', 'azure-cli-2.89.0-1.fc44.*.rpm']:
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(RuntimeError, 'does not match the requested artifact'):
                    rpm_package.verify_rpm_installation(pattern, 'python3')
        self.call.assert_not_called()

    def test_wrong_architecture(self):
        self.metadata = 'azure-cli 2.90.0 1.fc44 aarch64'
        with self.assertRaisesRegex(RuntimeError, 'architecture aarch64 does not match x86_64'):
            rpm_package.verify_rpm_installation('azure-cli-2.90.0-1.fc44.*.rpm', 'python3')

    def test_wrong_cli_version(self):
        self.version = '2.89.0'
        with self.assertRaisesRegex(RuntimeError, 'CLI version 2.89.0 does not match RPM version 2.90.0'):
            rpm_package.verify_rpm_installation()

    def test_wrong_python_dependency(self):
        self.requires = 'python3.12\n'
        for version in ['2.90.0', 'dev']:
            with self.subTest(version=version):
                self.metadata = f'azure-cli {version} 1.fc44 x86_64'
                with self.assertRaisesRegex(RuntimeError, 'does not require the selected Python package python3'):
                    rpm_package.verify_rpm_installation(python_package='python3')
        self.call.assert_not_called()

    def test_failed_cli_version_query_is_not_ignored(self):
        for version in ['2.90.0', 'dev']:
            with self.subTest(version=version):
                self.output.side_effect = [
                    f'azure-cli {version} 1.fc44 x86_64', self.arch,
                    subprocess.CalledProcessError(1, ['az', 'version'])
                ]
                with self.assertRaises(subprocess.CalledProcessError):
                    rpm_package.verify_rpm_installation()
        self.call.assert_not_called()

    def test_uninstalled_python_dependency_fails(self):
        self.call.side_effect = subprocess.CalledProcessError(1, ['rpm', '-q', 'python3'])
        with self.assertRaises(subprocess.CalledProcessError):
            rpm_package.verify_rpm_installation(python_package='python3')

    def test_invalid_or_multiple_installed_packages(self):
        for metadata in ['', 'other-cli 2.90.0 1.fc44 x86_64',
                         'azure-cli 2.90.0 1.fc44 x86_64 azure-cli 2.89.0 1.fc44 x86_64']:
            with self.subTest(metadata=metadata):
                self.metadata = metadata
                with self.assertRaisesRegex(RuntimeError, 'Expected one installed azure-cli RPM'):
                    rpm_package.verify_rpm_installation()

    def test_failed_package_query_is_not_ignored(self):
        self.output.side_effect = subprocess.CalledProcessError(1, ['rpm', '-q', 'azure-cli'])
        with self.assertRaises(subprocess.CalledProcessError):
            rpm_package.verify_rpm_installation()


if __name__ == '__main__':
    unittest.main()
