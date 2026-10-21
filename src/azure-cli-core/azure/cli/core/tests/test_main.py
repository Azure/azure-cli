# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


# Patch network-facing MSAL and ARM calls, without pre-importing Identity or persistence.
_AUTH_SETUP = """
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

# Some development installations cache Azure namespaces during site startup.
for name in tuple(sys.modules):
    if name == 'azure' or name.startswith('azure.'):
        del sys.modules[name]

import msal

def public_client(*args, **kwargs):
    spec = importlib.util.find_spec('redis')
    local_redis = str(Path.cwd() / 'redis')
    if spec and local_redis in (spec.submodule_search_locations or []):
        raise AssertionError('The working directory redis namespace reached authentication')
    from msal_extensions import PersistedTokenCache
    assert isinstance(kwargs['token_cache'], PersistedTokenCache)
    result = {
        'access_token': 'test-token',
        'id_token_claims': {
            'preferred_username': 'startup@example.invalid',
            'tid': '00000000-0000-0000-0000-000000000001'
        }
    }
    app = Mock()
    app.get_accounts.return_value = [{'username': 'startup@example.invalid'}]
    app.initiate_device_flow.return_value = {
        'user_code': 'test-code', 'message': 'Startup test device sign-in'
    }
    app.acquire_token_by_device_flow.return_value = result
    app.acquire_token_interactive.return_value = result
    return app

patch('msal.PublicClientApplication', side_effect=public_client).start()

subscription = SimpleNamespace(
    id='/subscriptions/00000000-0000-0000-0000-000000000002',
    display_name='Startup test', state='Enabled',
    tenant_id='00000000-0000-0000-0000-000000000001'
)
patch('azure.cli.core._profile.SubscriptionFinder.find_using_common_tenant',
      return_value=[subscription]).start()

from azure.cli.command_modules.resource import _client_factory
original_factory = _client_factory._resource_client_factory

def resource_client(cli_ctx, **kwargs):
    client = original_factory(cli_ctx, **kwargs)
    patch.object(type(client.resource_groups), 'list', return_value=iter([])).start()
    return client

patch.object(_client_factory, '_resource_client_factory', resource_client).start()
"""

_EXTENSION = """
from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import CliCommandType
import startup_explicit

def show():
    return {'explicit': startup_explicit.VALUE}

class StartupCommandsLoader(AzCommandsLoader):
    def __init__(self, cli_ctx=None):
        super().__init__(
            cli_ctx=cli_ctx,
            custom_command_type=CliCommandType(operations_tmpl=__name__ + '#{}'))

    def load_command_table(self, args):
        with self.command_group('startup-test') as group:
            group.custom_command('show', 'show')
        return self.command_table

    def load_arguments(self, command):
        pass

COMMAND_LOADER_CLS = StartupCommandsLoader
"""


class TestCliMain(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        (self.project / 'redis').mkdir()
        self.control = self.root / 'control'
        self.control.mkdir()
        self.config = self.root / 'config'
        self.config.mkdir()
        (self.config / 'config').write_text(
            '[core]\ncollect_telemetry = no\n'
            'encrypt_token_cache = no\nuse_msal_http_cache = no\n'
            'enable_broker_on_windows = no\n'
            '[auto-upgrade]\nenable = no\n', encoding='utf-8')
        fixture = self.root / 'imports'
        fixture.mkdir()
        (fixture / 'sitecustomize.py').write_text(textwrap.dedent(_AUTH_SETUP), encoding='utf-8')
        # Use the active loader's source so base-revision runs also reach subprocesses.
        main_spec = importlib.util.find_spec('azure.cli.__main__')
        main_source = main_spec.loader.get_source('azure.cli.__main__')
        for package in (fixture / 'azure', fixture / 'azure' / 'cli'):
            package.mkdir()
            (package / '__init__.py').write_text(
                "__path__ = __import__('pkgutil').extend_path(__path__, __name__)\n", encoding='utf-8')
        (package / '__main__.py').write_text(main_source, encoding='utf-8')
        self.repo = Path(__file__).resolve().parents[6]
        self.env = os.environ.copy()
        self.env.pop('PYTHONSAFEPATH', None)
        self.env.pop('PYTHONSTARTUP', None)
        self.env.update({
            'AZURE_CONFIG_DIR': str(self.config),
            'AZURE_EXTENSION_DIR': str(self.root / 'extensions'),
            'AZURE_EXTENSION_SYS_DIR': str(self.root / 'system-extensions'),
            'AZURE_CORE_NO_COLOR': 'true',
            'PYTHONPATH': os.pathsep.join([str(fixture)] + [
                str(self.repo / 'src' / package)
                for package in ('azure-cli', 'azure-cli-core', 'azure-cli-telemetry')
            ]),
        })

    def _invoke(self, args, cwd=None, launcher=False, safe_path=False):
        if launcher:
            command = [sys.executable, str(self.repo / 'src' / 'azure-cli' / 'az')]
        else:
            command = [sys.executable]
            if safe_path:
                command.append('-P')
            command += ['-m', 'azure.cli']
        result = subprocess.run(
            command + args, cwd=cwd or self.project, env=self.env,
            capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        return result

    def _login(self, cwd=None, launcher=False):
        result = self._invoke(['login', '--use-device-code'], cwd=cwd, launcher=launcher)
        self.assertIn('Startup test device sign-in', result.stderr)
        accounts = json.loads(result.stdout)
        self.assertEqual(accounts[0]['name'], 'Startup test')
        return accounts

    def test_login_from_redis_directory(self):
        accounts = self._login()
        account = json.loads(self._invoke(['account', 'show']).stdout)
        expected = dict(accounts[0])
        expected['environmentName'] = expected.pop('cloudName')
        self.assertEqual(account, expected)
        self.assertTrue((self.project / 'redis').is_dir())
        self.assertEqual(list((self.project / 'redis').iterdir()), [])
        self.assertIn('collect_telemetry = no', (self.config / 'config').read_text(encoding='utf-8'))

    def test_login_from_redis_directory_using_owned_launcher(self):
        self._login(launcher=True)

    def test_default_login_from_redis_directory(self):
        accounts = json.loads(self._invoke(['login']).stdout)
        self.assertEqual(accounts[0]['name'], 'Startup test')

    def test_group_list_from_redis_directory(self):
        # A cached account makes the original reproducer reach the real auth imports.
        self._login(cwd=self.control)
        self.assertEqual(json.loads(self._invoke(['group', 'list']).stdout), [])

    def test_login_equivalent_with_and_without_redis(self):
        self.assertEqual(self._login(cwd=self.control), self._login())

    def test_help_and_version_from_redis_directory(self):
        self._invoke(['--help'], cwd=self.control)  # Skip the first-run welcome banner.
        for args in (['--help'], ['version']):
            with self.subTest(args=args):
                control = self._invoke(args, cwd=self.control)
                project = self._invoke(args)
                self.assertEqual(control.stdout, project.stdout)
                self.assertTrue(project.stdout.strip())

    def _install_extension(self):
        extension = Path(self.env['AZURE_EXTENSION_DIR']) / 'startup-test'
        module = extension / 'azext_startup_test'
        module.mkdir(parents=True)
        (module / '__init__.py').write_text(textwrap.dedent(_EXTENSION), encoding='utf-8')
        metadata = extension / 'startup_test-1.0.0.dist-info'
        metadata.mkdir()
        (metadata / 'METADATA').write_text(
            'Metadata-Version: 2.1\nName: startup-test\nVersion: 1.0.0\n', encoding='utf-8')
        (self.project / 'startup_explicit.py').write_text("VALUE = 'preserved'\n", encoding='utf-8')

    def test_explicit_pythonpath_and_extension_imports(self):
        self._install_extension()
        pythonpath = self.env['PYTHONPATH']
        for path in (str(self.project), '.', ''):
            with self.subTest(path=path):
                self.env['PYTHONPATH'] = pythonpath + os.pathsep + path
                output = self._invoke(['startup-test', 'show']).stdout
                self.assertEqual(json.loads(output), {'explicit': 'preserved'})

    @unittest.skipUnless(hasattr(sys.flags, 'safe_path'), 'Python 3.11+ safe-path option')
    def test_safe_path_preserves_first_explicit_import(self):
        self._install_extension()
        self.env['PYTHONPATH'] = str(self.project) + os.pathsep + self.env['PYTHONPATH']
        output = self._invoke(['startup-test', 'show'], safe_path=True).stdout
        self.assertEqual(json.loads(output), {'explicit': 'preserved'})


if __name__ == '__main__':
    unittest.main()
