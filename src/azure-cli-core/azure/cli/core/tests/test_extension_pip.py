# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import unittest
from unittest import mock

from azure.cli.core.extension import operations
from azure.cli.core.mock import DummyCli
from azure.cli.core.tests.extension_pip_test_utils import (
    BACKEND_MODULE, BACKEND_NAME, DEPENDENCY_MODULE, DEPENDENCY_NAME,
    EXTENSION_MODULE, EXTENSION_NAME, ExtensionPipFixture, SENTINEL_ENV,
)
from azure.cli.core.util import CLIError


class TestExtensionPip(unittest.TestCase):

    def setUp(self):
        self.packages = ExtensionPipFixture(self)
        self.cli_ctx = DummyCli()
        self.assertIsNone(importlib.util.find_spec(BACKEND_MODULE))

    def _assert_installed(self, dependency_version):
        target = self.packages.target()
        versions = {
            dist.metadata['Name']: dist.version
            for dist in importlib.metadata.distributions(path=[str(target)])
        }
        self.assertEqual(versions, {EXTENSION_NAME: '1.0', DEPENDENCY_NAME: dependency_version})
        self.assertEqual(
            (target / DEPENDENCY_MODULE / '__init__.py').read_text(encoding='utf-8'),
            "__version__ = '{}'\n".format(dependency_version))
        self.assertTrue((target / EXTENSION_MODULE / '__init__.py').is_file())
        self.assertEqual(
            (target / self.packages.extension_wheel.name).read_bytes(), self.packages.extension_wheel.read_bytes())
        self.assertIsNone(importlib.util.find_spec(BACKEND_MODULE))
        self.assertFalse((target / (BACKEND_MODULE + '.py')).exists())

    def _assert_isolated_build(self):
        observation = json.loads(self.packages.build_log.read_text(encoding='utf-8'))
        self.assertEqual(observation['executable'], sys.executable)
        self.assertEqual(observation['sentinel'], os.environ[SENTINEL_ENV])
        self.assertIn('pip-build-env-', observation['backend_file'])
        self.assertIn('pip-build-env-', observation['pythonpath'])
        self.assertTrue(any('pip-build-env-' in path for path in observation['path']))
        self.assertIsNone(importlib.util.find_spec(BACKEND_MODULE))
        self.assertFalse((self.packages.target() / (BACKEND_MODULE + '.py')).exists())
        return observation

    def _assert_failed_install(self):
        with self.assertLogs(operations.logger, level='DEBUG') as logs:
            with self.assertRaises(CLIError) as failure:
                operations._add_whl_ext(self.cli_ctx, str(self.packages.extension_wheel))
        errors = [record.msg for record in logs.records if isinstance(record.msg, subprocess.CalledProcessError)]
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertGreater(error.returncode, 0)
        self.assertEqual(
            str(failure.exception),
            'An error occurred. Pip failed with status code {}. Use --debug for more information.'.format(
                error.returncode))
        self.assertTrue(any(record.msg == error.output for record in logs.records))
        self.assertFalse(self.packages.target().exists())
        self.assertTrue(self.packages.extension_wheel.is_file())
        return error

    def test_windows_prefers_compatible_wheel(self):
        with mock.patch.object(operations, 'IS_WINDOWS', True), \
                mock.patch.object(operations, 'check_output', wraps=subprocess.check_output) as run:
            name = operations._add_whl_ext(self.cli_ctx, str(self.packages.extension_wheel))

        self.assertEqual(name, EXTENSION_NAME)
        self._assert_installed('1.0')
        self.assertFalse(self.packages.build_log.exists())
        run.assert_called_once_with(
            [sys.executable, '-m', 'pip', 'install', '--target', str(self.packages.target()),
             str(self.packages.extension_wheel.resolve()),
             '--prefer-binary', '--disable-pip-version-check', '--no-cache-dir'],
            stderr=subprocess.STDOUT, universal_newlines=True)

    def test_non_windows_selects_newer_source(self):
        with mock.patch.object(operations, 'IS_WINDOWS', False), \
                mock.patch.object(operations, 'check_output', wraps=subprocess.check_output) as run:
            operations._add_whl_ext(self.cli_ctx, str(self.packages.extension_wheel))

        self._assert_installed('2.0')
        self._assert_isolated_build()
        self.assertNotIn('--prefer-binary', run.call_args.args[0])
        self.assertEqual(run.call_args.args[0][:3], [sys.executable, '-m', 'pip'])

    def test_windows_builds_source_only_dependency_with_isolation(self):
        self.packages.dependency_wheel.unlink()
        proxies = {'HTTP_PROXY': 'http://127.0.0.1:9', 'HTTPS_PROXY': 'http://127.0.0.1:10'}
        with mock.patch.object(operations, 'IS_WINDOWS', True), mock.patch.dict(os.environ, proxies):
            operations._add_whl_ext(self.cli_ctx, str(self.packages.extension_wheel))

        self._assert_installed('2.0')
        observation = self._assert_isolated_build()
        self.assertEqual(observation['http_proxy'], proxies['HTTP_PROXY'])
        self.assertEqual(observation['https_proxy'], proxies['HTTPS_PROXY'])

    def test_windows_respects_newer_source_requirement(self):
        self.packages.make_extension('>=2.0')
        with mock.patch.object(operations, 'IS_WINDOWS', True):
            operations._add_whl_ext(self.cli_ctx, str(self.packages.extension_wheel))

        self._assert_installed('2.0')
        self._assert_isolated_build()

    def test_windows_reports_unsupported_source_build_and_cleans_target(self):
        self.packages.make_extension('>=2.0')
        self.packages.make_sdist(unsupported=True)
        target = self.packages.target()
        target.mkdir(parents=True)
        (target / 'partial-install').write_text('remove on failure', encoding='utf-8')
        with mock.patch.object(operations, 'IS_WINDOWS', True):
            error = self._assert_failed_install()

        self.assertIn('Synthetic source build is unsupported', error.output)
        self._assert_isolated_build()

    def _embedded_python(self):
        if sys.implementation.name != 'cpython' or sys.version_info < (3, 11):
            self.skipTest('The ._pth reproduction requires CPython 3.11 or later')
        if sys.platform not in ('linux', 'win32'):
            self.skipTest('Copying the ._pth test interpreter is supported only on Linux and Windows')

        directory = self.packages.root / 'embedded'
        directory.mkdir()
        executable = directory / ('python.exe' if sys.platform == 'win32' else 'python')
        original = Path(getattr(sys, '_base_executable', sys.executable)).resolve()
        shutil.copy2(original, executable)
        self.assertFalse(executable.is_symlink())

        paths = [sysconfig.get_path('stdlib'), sysconfig.get_path('platstdlib'),
                 sysconfig.get_config_var('DESTSHARED')]
        paths.extend(path for path in sys.path if path.endswith('.zip'))
        paths.append(str(Path(importlib.util.find_spec('pip').origin).parent.parent))
        if sys.platform == 'win32':
            # A venv launcher alone is not a portable Windows runtime; copy the base runtime DLLs too.
            for runtime in {original.parent, Path(sys.base_prefix)}:
                for pattern in ('python*.dll', 'vcruntime*.dll'):
                    for dll in runtime.glob(pattern):
                        shutil.copy2(dll, directory / dll.name)
                paths.extend([str(runtime), str(runtime / 'DLLs')])
            if not list(directory.glob('python{}{}*.dll'.format(*sys.version_info[:2]))):
                self.skipTest('A standalone Windows CPython DLL layout is required for the copied interpreter')
        (directory / 'python._pth').write_text(
            '\n'.join(dict.fromkeys(path for path in paths if path)) + '\nimport site\n', encoding='utf-8')
        return str(executable)

    def test_embedded_python_backend_import_requires_wheel_preference(self):
        executable = self._embedded_python()
        pythonpath = self.packages.root / 'pythonpath'
        pythonpath.mkdir()
        (pythonpath / 'azcli_ignored_pythonpath.py').write_text('present = True\n', encoding='utf-8')
        with mock.patch.dict(os.environ, {'PYTHONPATH': str(pythonpath), 'PIP_VERBOSE': '1'}):
            probe = json.loads(subprocess.check_output([
                executable, '-c',
                "import importlib.util, json, os, pip, ssl, sys; "
                "print(json.dumps({'isolated': sys.flags.isolated, "
                "'ignore_environment': sys.flags.ignore_environment, 'no_site': sys.flags.no_site, "
                "'path': sys.path, 'pythonpath': os.environ['PYTHONPATH'], "
                "'finds_marker': importlib.util.find_spec('azcli_ignored_pythonpath') is not None, "
                "'finds_backend': importlib.util.find_spec('" + BACKEND_MODULE + "') is not None}))",
            ], stderr=subprocess.STDOUT, universal_newlines=True))
            self.assertEqual(probe['isolated'], 1)
            self.assertEqual(probe['ignore_environment'], 1)
            self.assertEqual(probe['no_site'], 0)
            self.assertEqual(probe['pythonpath'], str(pythonpath))
            self.assertNotIn(str(pythonpath), probe['path'])
            self.assertFalse(probe['finds_marker'])
            self.assertFalse(probe['finds_backend'])

            with mock.patch.object(sys, 'executable', executable):
                with mock.patch.object(operations, 'IS_WINDOWS', False):
                    error = self._assert_failed_install()
                self.assertEqual(error.cmd[:3], [executable, '-m', 'pip'])
                self.assertIn('Successfully installed {}-1.0'.format(BACKEND_NAME), error.output)
                self.assertRegex(error.output, r'Installing build dependencies[^\n]*done')
                self.assertIn('BackendUnavailable', error.output)
                self.assertIn(BACKEND_MODULE, error.output)
                self.assertFalse(self.packages.build_log.exists())

                with mock.patch.object(operations, 'IS_WINDOWS', True):
                    operations._add_whl_ext(self.cli_ctx, str(self.packages.extension_wheel))

        self._assert_installed('1.0')
        self.assertFalse(self.packages.build_log.exists())
