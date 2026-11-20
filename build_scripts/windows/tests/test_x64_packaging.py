# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


WINDOWS = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, WINDOWS / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EmbeddedPythonTests(unittest.TestCase):
    def setUp(self):
        self.validator = load_script('validate_python')
        build = (WINDOWS / 'scripts' / 'build.cmd').read_text(encoding='utf-8')
        version = re.search(r'(?im)^set\s+"?PYTHON_VERSION=(\d+\.\d+\.\d+)"?\s*$', build)
        self.assertIsNotNone(version, 'build.cmd must configure the embedded Python version')
        self.expected_version = version.group(1)
        self.version_info = tuple(map(int, self.expected_version.split('.')))

    def validate(self, version=None, platform='win-amd64', pointer_size=8, expected_version=None):
        with patch.object(sys, 'version_info', self.version_info if version is None else version), \
                patch.object(self.validator.sysconfig, 'get_platform', return_value=platform), \
                patch.object(self.validator.struct, 'calcsize', return_value=pointer_size), \
                contextlib.redirect_stderr(io.StringIO()) as errors:
            result = self.validator.main([
                self.expected_version if expected_version is None else expected_version
            ])
        return result, errors.getvalue()

    def test_exact_x64_version_is_accepted(self):
        self.assertEqual(self.validate(), (0, ''))

    def test_validator_accepts_versions_independent_of_build_pin(self):
        for version in ((3, 10, 1), (3, 15, 2)):
            with self.subTest(version=version):
                expected = '.'.join(map(str, version))
                self.assertEqual(self.validate(version=version, expected_version=expected), (0, ''))

    def test_invalid_arguments_report_usage_without_a_traceback(self):
        for arguments in ([], ['invalid'], ['3.14'], ['3.14.1', 'extra']):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()) as errors:
                with self.assertRaises(SystemExit) as raised:
                    self.validator.main(arguments)
                self.assertEqual(raised.exception.code, 2)
                self.assertIn('usage:', errors.getvalue())
                self.assertNotIn('Traceback', errors.getvalue())

    def test_stale_or_wrong_architecture_is_rejected(self):
        major, minor, patch_version = self.version_info
        for kwargs in ({'version': (major, minor, patch_version + 1)}, {'platform': 'win32', 'pointer_size': 4},
                       {'platform': 'win-arm64'}, {'pointer_size': 4}):
            with self.subTest(**kwargs):
                result, error = self.validate(**kwargs)
                self.assertEqual(result, 1)
                self.assertIn(f'Expected Python {self.expected_version} (win-amd64)', error)

    def test_build_checks_cache_before_pip_and_copy(self):
        build = (WINDOWS / 'scripts' / 'build.cmd').read_text(encoding='utf-8')
        self.assertTrue((WINDOWS / 'scripts' / 'validate_python.py').is_file())
        validation = build.index('"%PYTHON_EXE%" -I "%~dp0validate_python.py" "%PYTHON_VERSION%"')
        self.assertLess(validation, build.index('"%PYTHON_EXE%" -Im pip --version'))
        self.assertLess(validation, build.index('robocopy %PYTHON_DIR%'))
        self.assertIn('if %errorlevel% neq 0 (', build[validation:build.index('robocopy %PYTHON_DIR%')])
        self.assertIn('Move that directory aside', build)
        self.assertNotRegex(build.lower(), r'rmdir[^\n]*%python_dir%')


class PackagingConfigurationTests(unittest.TestCase):
    def test_build_defaults_and_supported_targets(self):
        build = (WINDOWS / 'scripts' / 'build.cmd').read_text()
        self.assertRegex(build, r'if "%ARCH%"=="" \(\s+set ARCH=x64')
        self.assertNotIn('set PYTHON_ARCH=win32', build)
        self.assertIn('if not "%TARGET%"=="msi" if not "%TARGET%"=="zip"', build)

    def test_wix_project_and_solution_are_x64_only(self):
        project = ET.parse(WINDOWS / 'azure-cli.wixproj')
        ns = {'m': 'http://schemas.microsoft.com/developer/msbuild/2003'}
        self.assertEqual(project.find('.//m:Platform', ns).text, 'x64')
        self.assertNotIn('|x86', (WINDOWS / 'azure-cli.wixproj').read_text(encoding='utf-8-sig'))
        self.assertNotIn('|x86', (WINDOWS / 'azure-cli.sln').read_text(encoding='utf-8-sig'))
        error = project.find(".//m:Target[@Name='BeforeBuild']/m:Error", ns)
        self.assertIn("'$(Platform)' != 'x64'", error.attrib['Condition'])

    def test_wix_keeps_x64_identities_and_x86_migration(self):
        product = (WINDOWS / 'Product.wxs').read_text()
        identities = {
            'UpgradeCode32': 'dff82af0-3f95-4ac9-8efd-948604fdb028',
            'UpgradeCode': '90762fec-9554-4729-a107-c6a8ea316698',
            'AzureCliRegistryGuid': '90b6367e-4e15-4313-af33-a0ef459a56fc',
            'AzureCliSystemPathGuid': '12c8f0dc-0475-4814-93b6-fcbe82e89532',
            'AzureCliVersionGuid': '4df4882f-4604-4cdc-a0b4-bffc4b8c5967',
            'RemoveAzureCLIFolderGuid': '7ce8a521-7429-4ded-9cce-0948e393cc83',
            'RemoveCLIFolderGuid': '59fb416c-91d0-49aa-a185-d4330c435a93',
        }
        for name, guid in identities.items():
            self.assertIn(f'<?define {name} = "{guid}" ?>', product)
        self.assertNotRegex(product, r'<\?(?:else)?if.*"x86"')
        self.assertIn('<?error Unsupported platform "$(var.Platform)" ?>', product)
        ns = {'w': 'http://schemas.microsoft.com/wix/2006/wi'}
        root = ET.fromstring(product)
        upgrade = root.find(".//w:Upgrade[@Id='$(var.UpgradeCode32)']", ns)
        versions = {item.attrib['Property']: item.attrib for item in upgrade}
        self.assertEqual(versions['WIX_X86_UPGRADE_DETECTED']['IncludeMaximum'], 'yes')
        self.assertEqual(versions['WIX_X86_DOWNGRADE_DETECTED']['OnlyDetect'], 'yes')
        self.assertEqual(versions['WIX_X86_DOWNGRADE_DETECTED']['IncludeMinimum'], 'no')
        self.assertIn('NOT (WIX_DOWNGRADE_DETECTED OR WIX_X86_DOWNGRADE_DETECTED)', product)
        self.assertIn('ProgramFiles64Folder', product)

    def test_installation_scripts_reject_unexpected_platform(self):
        for name in ('setup_msi_test.ps1', 'test_msi_installation.ps1', 'test_zip_installation.ps1'):
            with self.subTest(script=name):
                script = (WINDOWS / 'scripts' / name).read_text()
                self.assertIn("$env:PLATFORM -and $env:PLATFORM -cne 'x64'", script)
                self.assertIn('throw "Unsupported PLATFORM', script)
                self.assertNotIn(r'C:\Program Files (x86)', script)

    @unittest.skipUnless(os.name == 'nt', 'Requires cmd.exe')
    def test_build_rejects_retired_and_unknown_architectures_before_building(self):
        for arch in ('x86', 'arm64', 'invalid'):
            with self.subTest(arch=arch):
                env = dict(os.environ, ARCH=arch, CLI_VERSION='0.0.0')
                result = subprocess.run(
                    ['cmd.exe', '/d', '/c', str(WINDOWS / 'scripts' / 'build.cmd')],
                    env=env, capture_output=True, text=True, check=False, timeout=30)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Only x64 is supported', result.stdout)
                self.assertNotIn('Cleaning previous build artifacts', result.stdout)

    @unittest.skipUnless(os.name == 'nt', 'Requires cmd.exe')
    def test_build_rejects_unknown_target_before_building(self):
        env = dict(os.environ, ARCH='x64', TARGET='invalid', CLI_VERSION='0.0.0')
        result = subprocess.run(
            ['cmd.exe', '/d', '/c', str(WINDOWS / 'scripts' / 'build.cmd')],
            env=env, capture_output=True, text=True, check=False, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unsupported TARGET', result.stdout)
        self.assertNotIn('Cleaning previous build artifacts', result.stdout)


class PackageTestInterpreterTests(unittest.TestCase):
    def test_all_pytest_calls_use_inspected_interpreter(self):
        runner = load_script('test_msi_package')
        with patch.object(runner.sysconfig, 'get_platform', return_value='win-amd64'), \
                patch.object(runner.struct, 'calcsize', return_value=8), \
                patch.object(sys, 'argv', ['test_msi_package.py']), \
                patch.object(sys, 'executable', r'C:\retained\python.exe'), \
                patch.object(runner.os, 'listdir', return_value=['network', 'account']), \
                patch.object(runner.os.path, 'isdir', return_value=True), \
                patch.object(runner.subprocess, 'call', return_value=0) as call:
            self.assertEqual(runner.main(), 0)
        self.assertEqual(call.call_count, 3)
        for args in call.call_args_list:
            self.assertEqual(args.args[0][:3], [r'C:\retained\python.exe', '-m', 'pytest'])

    def test_non_x64_interpreter_is_rejected_before_tests(self):
        runner = load_script('test_msi_package')
        with patch.object(runner.sysconfig, 'get_platform', return_value='win32'), \
                patch.object(runner.subprocess, 'call') as call, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(), 1)
        call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
