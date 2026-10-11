# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import configparser
import copy
import csv
from email.parser import BytesParser
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import venv
import zipfile


CLI_SOURCE = Path(__file__).resolve().parents[5] / 'azure-cli'
WINDOWS = sys.platform == 'win32'
HELPER = 'az-cli.exe' if WINDOWS else 'az-cli'
POWERSHELL = shutil.which('powershell.exe') or shutil.which('pwsh')
UV = shutil.which('uv')

# Only the CLI payload is replaced: the wheel's launchers and entry point are installed unchanged.
PROBE_MAIN = b"""import json
import os
import sys

try:
    print(json.dumps({
        'executable': sys.executable,
        'prefix': sys.prefix,
        'args': sys.argv[1:],
        'argv0': sys.argv[0],
        'module': __name__,
        'spec': __spec__.name,
        'installer': os.environ.get('AZ_INSTALLER'),
        'pythonpath': os.environ.get('PYTHONPATH'),
    }))
    sys.exit(int(os.environ.get('AZ_LAUNCHER_TEST_EXIT', '0')))
finally:
    print('CLI finalized', file=sys.stderr)
"""

LEGACY_BATCH = b"""@echo off
setlocal
SET PYTHONPATH=%~dp0\\src;%PYTHONPATH%
SET AZ_INSTALLER=PIP
IF EXIST "%~dp0\\python.exe" (
  "%~dp0\\python.exe" -m azure.cli %*
) ELSE (
  python -m azure.cli %*
)
"""


def clean_environment():
    env = os.environ.copy()
    for name in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONUSERBASE', 'AZ_INSTALLER', 'VIRTUAL_ENV'):
        env.pop(name, None)
    return env


def run(command, cwd, env=None, check=True):
    result = subprocess.run(command, cwd=cwd, env=env or clean_environment(),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            encoding='utf-8', errors='replace', timeout=120, check=False)
    if check and result.returncode:
        raise AssertionError('{} failed ({}):\n{}\n{}'.format(
            command, result.returncode, result.stdout, result.stderr))
    return result


class TestLauncherEntryPoint(unittest.TestCase):

    def test_runs_cli_main_module(self):
        launcher = runpy.run_path(str(CLI_SOURCE / 'azure/cli/_launcher.py'))
        with patch('runpy.run_module') as run_module:
            launcher['main']()
        run_module.assert_called_once_with('azure.cli.__main__', run_name='__main__', alter_sys=True)


class TestInstalledLaunchers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.build_directory = tempfile.TemporaryDirectory(prefix='az-launcher-build-')
        cls.addClassCleanup(cls.build_directory.cleanup)
        cls.build_root = Path(cls.build_directory.name)
        source = cls.build_root / 'source'
        source.mkdir()
        # Build the real packaging configuration without copying unrelated command modules.
        files = (
            'setup.py', 'setup.cfg', 'azure_cli_bdist_wheel.py', 'MANIFEST.in',
            'README.rst', 'HISTORY.rst', 'LICENSE.txt', 'az', 'az.bat', 'az.completion.sh', 'azps.ps1',
            'azure/__init__.py', 'azure/cli/__init__.py', 'azure/cli/__main__.py',
            'azure/cli/_launcher.py', 'azure/cli/command_modules/__init__.py',
        )
        for name in files:
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(CLI_SOURCE / name, target)
        distributions = cls.build_root / 'dist'
        run([sys.executable, 'setup.py', '--quiet', 'sdist', '--dist-dir', str(distributions)], source)
        cls.sdist = next(distributions.glob('*.tar.gz'))
        unpacked = cls.build_root / 'unpacked'
        shutil.unpack_archive(str(cls.sdist), str(unpacked))
        unpacked_source = next(unpacked.iterdir())
        run([sys.executable, 'setup.py', '--quiet', 'bdist_wheel', '--dist-dir', str(distributions)],
            unpacked_source)
        cls.wheel = next(distributions.glob('*.whl'))
        cls.probe_wheel = cls.make_probe_wheel(cls.build_root / 'probe')
        cls.legacy_wheel = cls.make_probe_wheel(cls.build_root / 'legacy', legacy=True)

    @classmethod
    def make_probe_wheel(cls, directory, legacy=False):
        from wheel.wheelfile import WheelFile

        directory.mkdir()
        wheel_parts = cls.wheel.name.split('-')
        original_version = wheel_parts[1]
        version = original_version + '.dev0' if legacy else original_version
        wheel_parts[1] = version
        target = directory / '-'.join(wheel_parts)
        with zipfile.ZipFile(cls.wheel) as source, WheelFile(str(target), 'w') as output:
            for name in source.namelist():
                if name.endswith('.dist-info/RECORD'):
                    continue
                if legacy and (name.endswith('.dist-info/entry_points.txt') or
                               name == 'azure/cli/_launcher.py'):
                    continue
                content = source.read(name)
                if name == 'azure/cli/__main__.py':
                    content = PROBE_MAIN
                elif legacy and name.endswith('.data/scripts/az.bat'):
                    content = LEGACY_BATCH
                elif name.endswith('.dist-info/METADATA'):
                    metadata = BytesParser().parsebytes(content)
                    # Keep installer tests offline; the probe uses only the standard library.
                    del metadata['Requires-Dist']
                    metadata.replace_header('Version', version)
                    content = metadata.as_bytes()
                info = copy.copy(source.getinfo(name))
                info.filename = name.replace('azure_cli-' + original_version + '.',
                                             'azure_cli-' + version + '.', 1)
                output.writestr(info, content)
        return target

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='az-launcher-test-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.python, self.scripts = self.create_environment('tool')
        self.install(self.probe_wheel, self.python)
        self.other_python, self.other_scripts = self.create_environment('unrelated')
        self.install(self.probe_wheel, self.other_python)
        # PATH Python can even import Azure CLI; successful import is not installation identity.
        for name in ('az', 'az.bat'):
            (self.other_scripts / name).unlink()

    def create_environment(self, name):
        directory = self.root / name
        venv.EnvBuilder(with_pip=False).create(directory)
        scripts = directory / ('Scripts' if WINDOWS else 'bin')
        return scripts / ('python.exe' if WINDOWS else 'python'), scripts

    def install(self, wheel, python):
        run([sys.executable, '-I', '-m', 'pip', '--isolated', '--python', str(python),
             'install', '--no-index', '--no-deps', '--no-cache-dir', '--no-compile',
             '--disable-pip-version-check', '--force-reinstall', str(wheel)], self.root)

    def environment(self, scripts, exit_code=0):
        env = clean_environment()
        env['PATH'] = os.pathsep.join((str(self.other_scripts), str(scripts), env.get('PATH', '')))
        env['AZ_LAUNCHER_TEST_EXIT'] = str(exit_code)
        return env

    def expose(self, name='shared bin'):
        directory = self.root / name
        directory.mkdir(parents=True, exist_ok=True)
        for name in ('az', 'az.bat', HELPER):
            if (self.scripts / name).exists():
                shutil.copy2(self.scripts / name, directory / name)
        return directory

    def assert_probe(self, result, python, args, exit_code=0):
        self.assertEqual(result.returncode, exit_code, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(os.path.normcase(payload['executable']), os.path.normcase(str(python)))
        self.assertEqual(os.path.normcase(payload['prefix']), os.path.normcase(str(python.parent.parent)))
        self.assertEqual(payload['args'], args)
        self.assertEqual(payload['module'], '__main__')
        self.assertEqual(payload['spec'], 'azure.cli.__main__')
        self.assertTrue(payload['argv0'].endswith('__main__.py'))
        self.assertNotIn('RuntimeWarning', result.stderr)
        self.assertIn('CLI finalized', result.stderr)
        return payload

    def shell(self, shell, command, scripts, env=None):
        env = env or self.environment(scripts)
        if shell == 'cmd':
            comspec = os.environ.get('COMSPEC', 'cmd.exe')
            command = '"{}" /d /v:off /s /c "{}"'.format(comspec, command)
        else:
            command = [POWERSHELL, '-NoProfile', '-NonInteractive', '-Command',
                       '& ' + command + '; exit $LASTEXITCODE']
        return run(command, self.root, env, check=False)

    def test_wheel_and_sdist_include_entry_point_and_original_scripts(self):
        with zipfile.ZipFile(self.wheel) as wheel:
            names = wheel.namelist()
            for name in ('azure/cli/_launcher.py', 'azure/cli/__main__.py'):
                self.assertEqual(wheel.read(name), (CLI_SOURCE / name).read_bytes())
            entries = next(name for name in names if name.endswith('.dist-info/entry_points.txt'))
            config = configparser.ConfigParser()
            config.read_string(wheel.read(entries).decode())
            self.assertEqual(dict(config['console_scripts']), {'az-cli': 'azure.cli._launcher:main'})
            for script in ('az', 'az.bat', 'az.completion.sh', 'azps.ps1'):
                name = next(name for name in names if name.endswith('.data/scripts/' + script))
                # setuptools rewrites the Python shebang, but must retain the extensionless script.
                self.assertEqual(wheel.read(name).splitlines()[1:],
                                 (CLI_SOURCE / script).read_bytes().splitlines()[1:])
        with tarfile.open(self.sdist) as sdist:
            for name in ('azure/cli/_launcher.py', 'azure/cli/__main__.py'):
                member = next(member for member in sdist.getmembers() if member.name.endswith('/' + name))
                self.assertEqual(sdist.extractfile(member).read(), (CLI_SOURCE / name).read_bytes())

    def test_helper_retains_interpreter_after_relocation(self):
        args = ['--version', 'value with spaces', 'literal "quotes"', 'a&b', '', 'trailing\\']
        for scripts in (self.scripts, self.expose()):
            with self.subTest(scripts=scripts):
                result = run([str(scripts / HELPER), *args], self.root,
                             self.environment(scripts, exit_code=17), check=False)
                self.assert_probe(result, self.python, args, exit_code=17)

    def test_helper_supports_installation_path_with_spaces(self):
        python, scripts = self.create_environment('tool with spaces')
        self.install(self.probe_wheel, python)
        result = run([str(scripts / HELPER), 'version'], self.root, self.environment(scripts))
        self.assert_probe(result, python, ['version'])

    @unittest.skipIf(WINDOWS, 'The extensionless Windows script is exercised through Git Bash below.')
    def test_extensionless_launcher_preserves_environment_and_exit_status(self):
        for scripts in (self.scripts, self.expose()):
            for installer in (None, 'CUSTOM'):
                with self.subTest(scripts=scripts, installer=installer):
                    env = self.environment(scripts, exit_code=23)
                    existing = str(self.root / 'existing python path')
                    env['PYTHONPATH'] = existing
                    if installer:
                        env['AZ_INSTALLER'] = installer
                    result = run([str(scripts / 'az'), 'version', 'a b'], self.root, env, check=False)
                    payload = self.assert_probe(result, self.python, ['version', 'a b'], exit_code=23)
                    self.assertEqual(payload['installer'], installer or 'PIP')
                    self.assertEqual(payload['pythonpath'], os.pathsep.join((str(scripts / 'src'), existing)))

    def test_upgrade_replaces_legacy_batch_and_records_helper(self):
        self.install(self.legacy_wheel, self.python)
        self.assertFalse((self.scripts / HELPER).exists())
        shared = self.expose()
        self.assertEqual((shared / 'az.bat').read_bytes().splitlines(), LEGACY_BATCH.splitlines())
        if WINDOWS:
            result = self.shell('cmd', 'az version', shared)
            self.assert_probe(result, self.other_python, ['version'])
        self.install(self.probe_wheel, self.python)
        self.expose()
        self.assertEqual((shared / 'az.bat').read_bytes(), (self.scripts / 'az.bat').read_bytes())
        record_path = run([str(self.python), '-I', '-c',
                           "import importlib.metadata; d = importlib.metadata.distribution('azure-cli'); "
                           "print(d.read_text('RECORD'))"], self.root).stdout
        installed = [row[0] for row in csv.reader(io.StringIO(record_path)) if row]
        self.assertTrue(any(name.endswith('/' + HELPER) for name in installed))
        self.assertFalse((self.scripts / 'az.exe').exists())
        if WINDOWS:
            result = self.shell('cmd', 'az version', shared)
        else:
            result = run([str(shared / HELPER), 'version'], self.root, self.environment(shared))
        self.assert_probe(result, self.python, ['version'])

    @unittest.skipUnless(WINDOWS, 'Requires Windows cmd.exe.')
    def test_batch_uses_bound_interpreter_in_scripts_and_shared_layouts(self):
        layouts = (self.scripts, self.expose(), self.expose('base/Scripts'),
                   self.expose('user/Python/Scripts'))
        shells = ['cmd'] + (['powershell'] if POWERSHELL else [])
        for scripts in layouts:
            for shell in shells:
                for argument in ('version', '--version'):
                    with self.subTest(scripts=scripts, shell=shell, argument=argument):
                        env = self.environment(scripts)
                        existing = str(self.root / 'existing python path')
                        env['PYTHONPATH'] = existing
                        env['AZ_INSTALLER'] = 'CUSTOM'
                        result = self.shell(shell, 'az ' + argument, scripts, env)
                        payload = self.assert_probe(result, self.python, [argument])
                        self.assertEqual(payload['installer'], 'PIP')
                        paths = payload['pythonpath'].split(os.pathsep)
                        self.assertEqual(os.path.normpath(paths[0]), str(scripts / 'src'))
                        self.assertEqual(paths[1:], [existing])

    @unittest.skipUnless(WINDOWS, 'Requires Windows cmd.exe.')
    def test_batch_does_not_select_adjacent_unrelated_python(self):
        shared = self.expose()
        shutil.copy2(self.other_python, shared / 'python.exe')
        result = self.shell('cmd', 'az version', shared)
        self.assert_probe(result, self.python, ['version'])

    @unittest.skipUnless(WINDOWS, 'Requires Windows cmd.exe.')
    def test_batch_preserves_quoting_arguments_and_exit_status(self):
        shared = self.expose('shared bin with spaces')
        command = r'az version "value with spaces" "a&b" "literal \"quotes\"" "" "C:\trailing space\\"'
        args = ['version', 'value with spaces', 'a&b', 'literal "quotes"', '', 'C:\\trailing space\\']
        result = self.shell('cmd', command, shared, self.environment(shared, exit_code=19))
        self.assert_probe(result, self.python, args, exit_code=19)

    @unittest.skipUnless(WINDOWS and POWERSHELL, 'Requires Windows PowerShell.')
    def test_powershell_preserves_arguments_and_exit_status(self):
        shared = self.expose()
        result = self.shell('powershell', "az --version 'value with spaces' '\"a&b\"'", shared,
                            self.environment(shared, exit_code=19))
        self.assert_probe(result, self.python, ['--version', 'value with spaces', 'a&b'], exit_code=19)

    @unittest.skipUnless(WINDOWS, 'Requires Windows cmd.exe.')
    def test_missing_helper_reports_repair_without_path_fallback(self):
        shared = self.expose()
        (shared / HELPER).unlink()
        # An importable CLI and another az-cli.exe are both available on PATH.
        result = self.shell('cmd', 'az version', shared)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('Azure CLI launcher error:', result.stderr)
        self.assertIn('az-cli.exe', result.stderr)
        self.assertIn('Reinstall Azure CLI', result.stderr)

    @unittest.skipUnless(WINDOWS, 'Requires a native Windows executable launcher.')
    def test_missing_bound_interpreter_fails_without_path_fallback(self):
        shared = self.expose()
        self.python.rename(self.python.with_suffix('.missing'))
        result = self.shell('cmd', 'az --version', shared)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn(str(self.python).lower(), result.stderr.lower())

    @unittest.skipUnless(WINDOWS, 'Requires Git Bash on Windows.')
    def test_git_bash_extensionless_launcher(self):
        bash = shutil.which('bash')
        if not bash or 'git' not in bash.lower():
            self.skipTest('Git Bash is not on PATH.')
        env = self.environment(self.scripts)
        result = run([bash, '--noprofile', '--norc', '-c', 'exec "$1" --version',
                      'launcher-test', (self.scripts / 'az').as_posix()], self.root, env)
        payload = self.assert_probe(result, self.python, ['--version'])
        self.assertEqual(payload['installer'], 'PIP')

    @unittest.skipUnless(UV, 'Requires uv for the tool installer integration.')
    def test_uv_exposes_and_upgrades_both_launchers(self):
        shared = self.root / 'uv shared bin'
        tools = self.root / 'uv tools'
        env = self.environment(shared)
        env.update(UV_TOOL_DIR=str(tools), UV_TOOL_BIN_DIR=str(shared),
                   UV_CACHE_DIR=str(self.root / 'uv cache'), UV_PYTHON_DOWNLOADS='never')
        for wheel in (self.legacy_wheel, self.probe_wheel):
            run([UV, '--no-config', 'tool', 'install', '--no-index', '--force',
                 '--python', str(self.python), str(wheel)], self.root, env)
        self.assertTrue((shared / 'az.bat').is_file())
        self.assertTrue((shared / HELPER).is_file())
        tool_python = tools / 'azure-cli' / ('Scripts/python.exe' if WINDOWS else 'bin/python')
        for argument in ('version', '--version'):
            if WINDOWS:
                for shell in ['cmd'] + (['powershell'] if POWERSHELL else []):
                    result = self.shell(shell, 'az ' + argument, shared, env)
                    self.assert_probe(result, tool_python, [argument])
            else:
                result = run([str(shared / 'az'), argument], self.root, env)
                self.assert_probe(result, tool_python, [argument])
