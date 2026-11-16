# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import subprocess
from contextlib import ExitStack
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from pycomposefile import ComposeFile
import yaml

from azure.cli.command_modules.containerapp import custom
from azure.cli.core.azclierror import FileOperationError, InvalidArgumentValueError


class ContainerappComposeFilePathsTest(unittest.TestCase):
    def setUp(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.project = self.directory / 'project'
        self.project.mkdir()
        self.compose_path = self.project / 'compose.yml'
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.project)

        # pycomposefile keeps its service ordering on the class.
        ComposeFile.ordered_services.clear()
        self.addCleanup(ComposeFile.ordered_services.clear)
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.environment = stack.enter_context(mock.patch.object(custom, 'show_managed_environment'))
        self.environment.return_value = {'id': 'test-environment', 'properties': {}}
        self.deployment = stack.enter_context(mock.patch.object(custom, 'create_containerapp'))
        self.deployment.side_effect = lambda *args, **kwargs: kwargs

    def deploy(self, compose):
        self.compose_path.write_text(yaml.safe_dump(compose, sort_keys=False), encoding='utf-8')
        return custom.create_containerapps_from_compose(
            cmd=None,
            resource_group_name='test-group',
            managed_env='test-environment',
            compose_file_path=str(self.compose_path))

    def test_containerapp_compose_rejects_secret_outside_project_before_deployment(self):
        outside = self.directory / 'outside.txt'
        outside.write_text('test-only-value', encoding='utf-8')
        compose = {
            'services': {'app': {'image': 'example/app:latest', 'secrets': ['test_secret']}},
            'secrets': {'test_secret': {'file': '../outside.txt'}}
        }

        with mock.patch('builtins.open', wraps=open) as read_file:
            with self.assertRaisesRegex(InvalidArgumentValueError, 'secrets.*test_secret'):
                self.deploy(compose)

        self.assertNotIn(mock.call('../outside.txt'), read_file.call_args_list)
        self.environment.assert_not_called()
        self.deployment.assert_not_called()

    def test_containerapp_compose_rejects_env_file_outside_project_before_reading(self):
        (self.project / 'inside.env').write_text('INSIDE=test-value\n', encoding='utf-8')
        (self.directory / 'outside.env').write_text('OUTSIDE=test-only-value\n', encoding='utf-8')
        compose = {
            'services': {'app': {
                'image': 'example/app:latest',
                'env_file': ['inside.env', '../outside.env']
            }}
        }

        with mock.patch('builtins.open', wraps=open) as read_file:
            with self.assertRaisesRegex(InvalidArgumentValueError, 'services.app.env_file'):
                self.deploy(compose)

        self.assertNotIn(mock.call('inside.env'), read_file.call_args_list)
        self.assertNotIn(mock.call('../outside.env'), read_file.call_args_list)
        self.environment.assert_not_called()
        self.deployment.assert_not_called()

    def test_containerapp_compose_reports_unreadable_file_before_deployment(self):
        secret_path = self.project / 'secret.txt'
        secret_path.write_text('test-only-value', encoding='utf-8')
        compose = {
            'services': {'app': {'image': 'example/app:latest', 'secrets': ['test_secret']}},
            'secrets': {'test_secret': {'file': 'secret.txt'}}
        }
        open_file = open

        def deny_secret(file, *args, **kwargs):
            if os.fspath(file) == str(secret_path.resolve()):
                raise PermissionError('Permission denied')
            return open_file(file, *args, **kwargs)

        with mock.patch('builtins.open', side_effect=deny_secret):
            with self.assertRaisesRegex(FileOperationError, "service 'app'"):
                self.deploy(compose)

        self.environment.assert_not_called()
        self.deployment.assert_not_called()

    def test_containerapp_compose_resolves_files_relative_to_compose_file(self):
        config = self.project / 'config'
        config.mkdir()
        (config / 'secret.txt').write_text('test-only-value\n', encoding='utf-8')
        (config / 'first.env').write_text('# comment\nFIRST=first\nSHARED=first\n', encoding='utf-8')
        (config / 'second.env').write_text('SECOND=second\nSHARED=second\n', encoding='utf-8')
        compose = {
            'services': {'app': {
                'image': 'example/app:latest',
                'env_file': ['config/first.env', 'config/second.env'],
                'environment': {'SHARED': 'explicit', 'INLINE': 'inline'},
                'secrets': [{'source': 'test_secret', 'target': 'app_secret'}]
            }},
            'secrets': {'test_secret': {'file': 'config/secret.txt'}}
        }
        os.chdir(self.directory)
        (self.directory / 'config').mkdir()
        (self.directory / 'config' / 'secret.txt').write_text('wrong-directory', encoding='utf-8')

        result = self.deploy(compose)

        self.assertEqual(result[0]['secrets'], ['app-secret=test-only-value\n'])
        self.assertEqual(result[0]['env_vars'], [
            'FIRST=first', 'SHARED=explicit', 'SECOND=second', 'INLINE=inline',
            'app-secret=secretref:app-secret'
        ])

    def test_containerapp_compose_accepts_single_env_file(self):
        (self.project / 'app.env').write_text('SETTING=test-value\n', encoding='utf-8')
        compose = {'services': {'app': {'image': 'example/app:latest', 'env_file': './app.env'}}}

        self.assertEqual(self.deploy(compose)[0]['env_vars'], ['SETTING=test-value'])

    def test_containerapp_compose_preserves_environment_without_files(self):
        compose = {'services': {'app': {
            'image': 'example/app:latest', 'environment': {'SETTING': 'test-value'}
        }}}

        self.assertEqual(self.deploy(compose)[0]['env_vars'], ['SETTING=test-value'])

    def test_containerapp_compose_accepts_shared_secret(self):
        (self.project / 'secret.txt').write_text('test-only-value', encoding='utf-8')
        compose = {
            'services': {
                'first': {'image': 'example/app:latest', 'secrets': ['test_secret']},
                'second': {'image': 'example/app:latest', 'secrets': ['test_secret']}
            },
            'secrets': {'test_secret': {'file': './secret.txt'}}
        }

        result = self.deploy(compose)

        self.assertEqual([app['secrets'] for app in result], [
            ['test-secret=test-only-value'], ['test-secret=test-only-value']
        ])

    def test_containerapp_compose_does_not_read_unused_secrets(self):
        compose = {
            'services': {'app': {'image': 'example/app:latest'}},
            'secrets': {
                'unused': {'file': '../does-not-exist.txt'},
                'external': {'external': True}
            }
        }

        self.assertIsNone(self.deploy(compose)[0]['secrets'])

    def assert_rejected_file(self, file_path, pattern='directory|regular file|Unable to resolve'):
        configurations = [
            {
                'services': {'app': {'image': 'example/app:latest', 'secrets': ['test_secret']}},
                'secrets': {'test_secret': {'file': file_path}}
            },
            {'services': {'app': {'image': 'example/app:latest', 'env_file': file_path}}}
        ]
        for compose in configurations:
            with self.subTest(compose=compose):
                with mock.patch('builtins.open', wraps=open) as read_file:
                    with self.assertRaisesRegex(InvalidArgumentValueError, pattern):
                        self.deploy(compose)
                self.assertEqual([os.fspath(call.args[0]) for call in read_file.call_args_list],
                                 [str(self.compose_path)])
                self.environment.assert_not_called()
                self.deployment.assert_not_called()

    def test_containerapp_compose_rejects_absolute_files_even_inside_project(self):
        secret_path = self.project / 'secret.txt'
        secret_path.write_text('test-only-value', encoding='utf-8')

        self.assert_rejected_file(str(secret_path), 'relative file path')

    def test_containerapp_compose_rejects_sibling_with_matching_directory_prefix(self):
        sibling = self.directory / 'project-other'
        sibling.mkdir()
        (sibling / 'file.txt').write_text('test-only-value', encoding='utf-8')

        self.assert_rejected_file('../project-other/file.txt')

    def test_containerapp_compose_rejects_missing_files(self):
        self.assert_rejected_file('missing.txt', 'Unable to resolve')

    def test_containerapp_compose_rejects_directory_references(self):
        self.assert_rejected_file('.', 'regular file')

    def test_containerapp_compose_rejects_undefined_secrets(self):
        compose = {'services': {'app': {'image': 'example/app:latest', 'secrets': ['undefined']}}}

        with self.assertRaisesRegex(InvalidArgumentValueError, 'undefined secret'):
            self.deploy(compose)

        self.environment.assert_not_called()
        self.deployment.assert_not_called()

    def test_containerapp_compose_validates_all_services_before_reading_files(self):
        (self.project / 'safe.txt').write_text('test-only-value', encoding='utf-8')
        (self.directory / 'outside.env').write_text('OUTSIDE=test-only-value\n', encoding='utf-8')
        compose = {
            'services': {
                'first': {'image': 'example/app:latest', 'secrets': ['test_secret']},
                'second': {'image': 'example/app:latest', 'env_file': '../outside.env'}
            },
            'secrets': {'test_secret': {'file': 'safe.txt'}}
        }

        with mock.patch('builtins.open', wraps=open) as read_file:
            with self.assertRaisesRegex(InvalidArgumentValueError, 'services.second.env_file'):
                self.deploy(compose)

        self.assertEqual([os.fspath(call.args[0]) for call in read_file.call_args_list],
                         [str(self.compose_path)])
        self.environment.assert_not_called()
        self.deployment.assert_not_called()

    def test_containerapp_compose_accepts_normalized_relative_files(self):
        (self.project / 'config').mkdir()
        (self.project / 'secret.txt').write_text('test-only-value', encoding='utf-8')
        compose = {
            'services': {'app': {'image': 'example/app:latest', 'secrets': ['test_secret']}},
            'secrets': {'test_secret': {'file': 'config/../secret.txt'}}
        }

        self.assertEqual(self.deploy(compose)[0]['secrets'], ['test-secret=test-only-value'])

    def create_symlink(self, link, target, is_directory=False):
        try:
            link.symlink_to(target, target_is_directory=is_directory)
        except OSError as ex:
            if os.name == 'nt' and ex.winerror == 1314:
                self.skipTest('Creating symbolic links requires Windows developer mode or privilege.')
            raise

    def test_containerapp_compose_rejects_symlink_to_outside_file(self):
        outside = self.directory / 'outside.txt'
        outside.write_text('test-only-value', encoding='utf-8')
        self.create_symlink(self.project / 'link.txt', outside)

        self.assert_rejected_file('link.txt')

    def test_containerapp_compose_rejects_symlink_directory_to_outside(self):
        outside = self.directory / 'outside'
        outside.mkdir()
        (outside / 'file.txt').write_text('test-only-value', encoding='utf-8')
        self.create_symlink(self.project / 'link', outside, is_directory=True)

        self.assert_rejected_file('link/file.txt')

    def test_containerapp_compose_accepts_symlink_to_inside_file(self):
        (self.project / 'secret.txt').write_text('test-only-value', encoding='utf-8')
        self.create_symlink(self.project / 'link.txt', self.project / 'secret.txt')
        compose = {
            'services': {'app': {'image': 'example/app:latest', 'secrets': ['test_secret']}},
            'secrets': {'test_secret': {'file': 'link.txt'}}
        }

        self.assertEqual(self.deploy(compose)[0]['secrets'], ['test-secret=test-only-value'])

    @unittest.skipUnless(os.name == 'nt', 'Windows path semantics')
    def test_containerapp_compose_rejects_windows_external_paths(self):
        (self.directory / 'outside.txt').write_text('test-only-value', encoding='utf-8')
        for path in [r'..\outside.txt', r'C:outside.txt', r'\outside.txt',
                     r'Z:\outside.txt', r'\\server\share\outside.txt']:
            with self.subTest(path=path):
                self.assert_rejected_file(path)

    @unittest.skipUnless(os.name == 'nt', 'Windows directory junctions')
    def test_containerapp_compose_rejects_junction_to_outside(self):
        outside = self.directory / 'outside'
        outside.mkdir()
        (outside / 'file.txt').write_text('test-only-value', encoding='utf-8')
        link = self.project / 'link'
        subprocess.run(
            [os.environ['COMSPEC'], '/c', 'mklink', '/J', str(link), str(outside)],
            check=True, capture_output=True)

        self.assert_rejected_file('link/file.txt')

    def invoke_cli(self, compose):
        from azure.cli.core import get_default_cli

        self.compose_path.write_text(yaml.safe_dump(compose, sort_keys=False), encoding='utf-8')
        config_directory = str(self.directory / 'cli-config')
        environment_id = (
            '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/test-group'
            '/providers/Microsoft.App/managedEnvironments/test-environment')
        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', config_directory), \
                mock.patch.multiple(
                    'azure.cli.core.extension',
                    EXTENSIONS_DIR=str(self.directory / 'extensions'),
                    EXTENSIONS_SYS_DIR=str(self.directory / 'system-extensions'),
                    DEV_EXTENSION_SOURCES=[]), \
                mock.patch.dict(os.environ, {
                    'AZURE_CONFIG_DIR': config_directory,
                    'AZURE_EXTENSION_DIR': str(self.directory / 'extensions'),
                    'AZURE_EXTENSION_USE_DYNAMIC_INSTALL': 'no',
                    'AZURE_CORE_COLLECT_TELEMETRY': 'no',
                    'AZURE_CORE_CHECK_VERSION': 'no'
                }), \
                mock.patch('socket.socket.connect', side_effect=AssertionError('Network access is not allowed')):
            cli = get_default_cli()
            exit_code = cli.invoke([
                'containerapp', 'compose', 'create', '--resource-group', 'test-group',
                '--environment', environment_id, '--compose-file-path', str(self.compose_path),
                '--only-show-errors'
            ], out_file=StringIO())
        return exit_code, cli.result

    def test_containerapp_compose_cli_returns_error_for_outside_file(self):
        (self.directory / 'outside.env').write_text('OUTSIDE=test-only-value\n', encoding='utf-8')
        compose = {'services': {'app': {
            'image': 'example/app:latest', 'env_file': '../outside.env'
        }}}

        exit_code, result = self.invoke_cli(compose)

        self.assertNotEqual(exit_code, 0)
        self.assertIsInstance(result.error, InvalidArgumentValueError)
        self.environment.assert_not_called()
        self.deployment.assert_not_called()

    def test_containerapp_compose_cli_deploys_project_file_from_other_directory(self):
        (self.project / 'app.env').write_text('SETTING=test-value\n', encoding='utf-8')
        compose = {'services': {'app': {'image': 'example/app:latest', 'env_file': 'app.env'}}}
        os.chdir(self.directory)

        exit_code, result = self.invoke_cli(compose)

        self.assertEqual(exit_code, 0)
        self.assertEqual(result.result[0]['env_vars'], ['SETTING=test-value'])
