# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import hashlib
import json
import ntpath
import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from azure.cli.core.azclierror import ClientRequestError
from azure.cli.command_modules.mysql import _util as mysql
from azure.cli.command_modules.mysql import custom as mysql_commands
from azure.cli.command_modules.postgresql.commands import deploy_commands as postgresql_commands
from azure.cli.command_modules.postgresql.utils import _flexible_server_util as postgresql
from azure.cli.command_modules.rdbms import _flexible_server_util as rdbms
from azure.cli.command_modules.rdbms import flexible_server_custom_common as rdbms_commands


MODULES = (mysql, postgresql, rdbms)


class DeploySetupTest(unittest.TestCase):

    def setUp(self):
        for module in MODULES:
            resolver = patch.object(module, 'resolve_executable', side_effect=lambda executable: executable)
            resolver.start()
            self.addCleanup(resolver.stop)
        resolver = patch.object(postgresql_commands, 'resolve_executable', side_effect=lambda executable: executable)
        resolver.start()
        self.addCleanup(resolver.stop)
        self.cmd = SimpleNamespace(cli_ctx=object())
        self.server = SimpleNamespace(
            id='/subscriptions/test-sub/resourceGroups/test-rg/'
               'providers/Microsoft.DBforMySQL/flexibleServers/test-server',
            name='test-server',
            fully_qualified_domain_name='test.invalid')
        self.secret = 'dummy-"quoted"\\secret\n\u00e9'
        self.repository = 'test-owner/test-repository'

    def _app(self):
        return {
            'appId': 'test-app',
            'password': self.secret,
            'tenant': 'test-tenant',
            'displayName': 'test-display',
            'name': 'test-name',
        }

    def _register(self, module, kind):
        if kind == 'credential':
            module.register_credential_secrets(
                self.cmd, 'postgresql' if module is postgresql else 'mysql',
                self.server, self.repository)
        else:
            kwargs = dict(
                server=self.server, database_name='test-db',
                administrator_login='test-user', administrator_login_password=self.secret,
                repository=self.repository, connection_string_name='TEST_CONNECTION')
            if module is not mysql:
                kwargs.update(cmd=self.cmd, database_engine='postgresql' if module is postgresql else 'mysql')
            module.register_connection_secrets(**kwargs)

    def test_registration_uses_standard_input(self):
        for module in MODULES:
            for kind in ('credential', 'connection'):
                with self.subTest(module=module.__name__, kind=kind), \
                        patch.object(module, 'create_service_principal_for_rbac', return_value=self._app()), \
                        patch.object(module, 'get_subscription_id', return_value='test-sub'), \
                        patch.object(module, 'open', create=True) as open_file, \
                        patch.object(module.os, 'remove') as remove_file, \
                        patch.object(module.subprocess, 'run', return_value=Mock(returncode=0)) as run:
                    self._register(module, kind)
                    open_file.assert_not_called()
                    remove_file.assert_not_called()
                    name = 'AZURE_CREDENTIALS' if kind == 'credential' else 'TEST_CONNECTION'
                    self.assertEqual(
                        run.call_args.args,
                        (['gh', 'secret', 'set', name, '--repo', self.repository],))
                    kwargs = run.call_args.kwargs
                    self.assertEqual(kwargs['stdout'], subprocess.DEVNULL)
                    self.assertEqual(kwargs['stderr'], subprocess.DEVNULL)
                    self.assertFalse(kwargs.get('shell', False))
                    self.assertIsInstance(kwargs['input'], bytes)
                    if kind == 'credential':
                        self.assertEqual(json.loads(kwargs['input']), {
                            'clientId': 'test-app', 'clientSecret': self.secret,
                            'tenantId': 'test-tenant', 'subscriptionId': 'test-sub'})
                    else:
                        value = kwargs['input'].decode('utf-8')
                        self.assertIn(self.secret, value)
                        self.assertIn('test.invalid', value)
                        self.assertIn('test-db', value)
                        self.assertIn('test-user', value)

    def test_registration_failure_does_not_report_success(self):
        for module in MODULES:
            for kind in ('credential', 'connection'):
                for failure in (FileNotFoundError('gh missing'), PermissionError('launch denied'),
                                OSError('pipe failure'), 'nonzero'):
                    with self.subTest(module=module.__name__, kind=kind, failure=str(failure)), \
                            patch.object(module, 'create_service_principal_for_rbac', return_value=self._app()), \
                            patch.object(module, 'get_subscription_id', return_value='test-sub'), \
                            patch.object(module, 'open', create=True) as open_file, \
                            patch.object(module.os, 'remove') as remove_file, \
                            patch.object(module, 'logger') as logger, \
                            patch.object(module.subprocess, 'run') as run:
                        if failure == 'nonzero':
                            run.return_value = Mock(returncode=1, stdout=self.secret, stderr=self.secret)
                            error_type = ClientRequestError
                        else:
                            run.side_effect = failure
                            error_type = type(failure)
                        with self.assertRaises(error_type) as raised:
                            self._register(module, kind)
                        self.assertNotIn(self.secret, str(raised.exception))
                        self.assertNotIn(self.secret, str(logger.mock_calls))
                        self.assertNotIn('Added secret', str(logger.mock_calls))
                        open_file.assert_not_called()
                        remove_file.assert_not_called()

    def test_upload_failure_stops_workflow_generation(self):
        for module in MODULES:
            with self.subTest(module=module.__name__), \
                    patch.object(module, 'get_git_root_dir', return_value='test-root'), \
                    patch.object(module.os.path, 'exists', return_value=True), \
                    patch.object(module, 'run_cmd', return_value=Mock(stdout=b'')), \
                    patch.object(module, 'create_service_principal_for_rbac', return_value=self._app()), \
                    patch.object(module, 'get_subscription_id', return_value='test-sub'), \
                    patch.object(module.subprocess, 'run', return_value=Mock(returncode=1)), \
                    patch.object(module, 'register_connection_secrets') as connection, \
                    patch.object(module, 'open', create=True) as open_file:
                with self.assertRaises(ClientRequestError):
                    module.fill_action_template(
                        self.cmd, 'mysql', self.server, 'test-db', 'test-user',
                        self.secret, 'query.sql', 'test-action', self.repository)
                connection.assert_not_called()
                open_file.assert_not_called()

    def test_stdin_round_trip_with_local_process(self):
        payload = self.secret.encode('utf-8')
        digest = hashlib.sha256(payload).hexdigest()
        script = (
            'import hashlib, sys; '
            'sys.exit(0 if hashlib.sha256(sys.stdin.buffer.read()).hexdigest() == sys.argv[1] else 1)'
        )
        for module in MODULES:
            with self.subTest(module=module.__name__):
                module.run_subprocess([sys.executable, '-c', script, digest], input_data=payload)

    def test_setup_stops_before_git_commit_on_upload_failure(self):
        self.server.network = SimpleNamespace(public_network_access='Enabled')
        for commands in (mysql_commands, postgresql_commands):
            with self.subTest(module=commands.__name__), \
                    patch.object(commands, 'gitcli_check_and_login'), \
                    patch.object(commands, 'fill_action_template', side_effect=ClientRequestError('Upload failed')), \
                    patch.object(commands, 'run_subprocess') as run:
                with self.assertRaises(ClientRequestError):
                    commands.github_actions_setup(
                        self.cmd, Mock(get=Mock(return_value=self.server)),
                        'test-rg', 'test-server', 'test-db', 'test-user', self.secret,
                        'query.sql', self.repository)
                run.assert_not_called()

    def test_missing_gh_stops_setup(self):
        self.server.network = SimpleNamespace(public_network_access='Enabled')
        for commands in (mysql_commands, postgresql_commands):
            with self.subTest(module=commands.__name__), \
                    patch.object(commands, 'run_cmd', side_effect=FileNotFoundError('gh missing')), \
                    patch.object(commands, 'fill_action_template') as fill, \
                    patch.object(commands, 'run_subprocess') as run:
                with self.assertRaises(ClientRequestError):
                    commands.github_actions_setup(
                        self.cmd, Mock(get=Mock(return_value=self.server)),
                        'test-rg', 'test-server', 'test-db', 'test-user', self.secret,
                        'query.sql', self.repository)
                fill.assert_not_called()
                run.assert_not_called()

    def test_empty_input_still_uses_pipe(self):
        for module in MODULES:
            with self.subTest(module=module.__name__), \
                    patch.object(module.subprocess, 'run', return_value=Mock(returncode=0)) as run, \
                    patch.object(module.subprocess, 'Popen') as popen:
                module.run_subprocess(['gh', 'secret', 'set', 'EMPTY'], input_data=b'')
                self.assertEqual(run.call_args.kwargs['input'], b'')
                popen.assert_not_called()

    def test_stdin_uses_resolved_executable_without_mutating_arguments(self):
        command = ['gh', 'secret', 'set', 'TEST_CONNECTION', '--repo', self.repository]
        original = list(command)
        executable = r'C:\Program Files\GitHub CLI\gh.exe'
        payload = self.secret.encode('utf-8')
        for module in MODULES:
            with self.subTest(module=module.__name__), \
                    patch.object(module, 'resolve_executable', return_value=executable) as resolve, \
                    patch.object(module.subprocess, 'run', return_value=Mock(returncode=0)) as run:
                module.run_subprocess(command, input_data=payload)
                resolve.assert_called_once_with('gh')
                run.assert_called_once_with(
                    [executable] + original[1:], input=payload,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.assertEqual(command, original)

    def test_stdin_stops_when_executable_resolution_fails(self):
        command = ['gh', 'secret', 'set', 'TEST_CONNECTION']
        original = list(command)
        for module in MODULES:
            with self.subTest(module=module.__name__), \
                    patch.object(module, 'resolve_executable', side_effect=FileNotFoundError('gh')) as resolve, \
                    patch.object(module.subprocess, 'run') as run, \
                    patch.object(module.subprocess, 'Popen') as popen:
                with self.assertRaises(FileNotFoundError):
                    module.run_subprocess(command, input_data=self.secret.encode('utf-8'))
                resolve.assert_called_once_with('gh')
                run.assert_not_called()
                popen.assert_not_called()
                self.assertEqual(command, original)

    def test_existing_nonsecret_commands_keep_their_behavior(self):
        for module in MODULES:
            for show_output in (False, True):
                with self.subTest(module=module.__name__, show_output=show_output), \
                        patch.object(module.subprocess, 'Popen') as popen, \
                        patch.object(module.subprocess, 'run') as run:
                    popen.return_value.returncode = 0
                    command = ['git', 'status']
                    module.run_subprocess(command, stdout_show=show_output)
                    kwargs = {} if show_output else dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if module is postgresql:
                        kwargs['shell'] = False
                    popen.assert_called_once_with(['git', 'status'], **kwargs)
                    popen.return_value.wait.assert_called_once_with()
                    run.assert_not_called()

    def test_existing_nonsecret_failure_still_logs_warning(self):
        for module in MODULES:
            with self.subTest(module=module.__name__), \
                    patch.object(module.subprocess, 'Popen') as popen, \
                    patch.object(module, 'logger') as logger:
                popen.return_value.returncode = 1
                popen.return_value.stderr.read.return_value = b'nonsecret failure\n'
                command = ['git', 'status']
                module.run_subprocess(command)
                logger.warning.assert_called_once_with('nonsecret failure')

    def test_workflow_run_preserves_quoted_names_and_branches(self):
        action = 'deploy "quoted" --repo other/repo'
        branch = 'feature "quoted" --ref other-branch'
        for commands in (mysql_commands, postgresql_commands, rdbms_commands):
            with self.subTest(module=commands.__name__), \
                    patch.object(commands, 'gitcli_check_and_login', return_value='gh'), \
                    patch.object(commands, 'run_subprocess') as run:
                commands.github_actions_run(action, branch)
                run.assert_called_once_with(['gh', 'workflow', 'run', action + '.yml', '--ref', branch])

    def test_setup_preserves_git_paths_and_branch_arguments(self):
        self.server.network = SimpleNamespace(public_network_access='Enabled')
        root = os.path.abspath('project with spaces')
        action = 'deploy "quoted" --repo other/repo'
        branch = 'feature "quoted" --ref other-branch'
        for commands, module in ((mysql_commands, mysql), (postgresql_commands, postgresql)):
            with self.subTest(module=commands.__name__), \
                    patch.object(commands, 'gitcli_check_and_login'), \
                    patch.object(commands, 'fill_action_template'), \
                    patch.object(commands, 'get_git_root_dir', return_value=root), \
                    patch.object(commands, 'run_subprocess') as run:
                commands.github_actions_setup(
                    self.cmd, Mock(get=Mock(return_value=self.server)),
                    'test-rg', 'test-server', 'test-db', 'test-user', self.secret,
                    'query.sql', self.repository, action_name=action, branch=branch, allow_push=True)
                action_path = root + module.GITHUB_ACTION_PATH + action + '.yml'
                self.assertEqual(run.call_args_list, [
                    unittest.mock.call(['git', 'add', action_path]),
                    unittest.mock.call(['git', 'commit', '-m', 'Add github action file']),
                    unittest.mock.call(['git', 'push', 'origin', branch]),
                ])

    def test_interactive_login_uses_argument_list(self):
        for commands in (mysql_commands, postgresql_commands, rdbms_commands):
            with self.subTest(module=commands.__name__), \
                    patch.object(commands, 'run_cmd', side_effect=[Mock(returncode=0), Mock(returncode=1)]), \
                    patch.object(commands, 'run_subprocess') as run:
                commands.gitcli_check_and_login()
                run.assert_called_once_with(['gh', 'auth', 'login'], stdout_show=True)


class WindowsDeploymentResolverTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='installed tools ')
        self.addCleanup(temporary.cleanup)
        self.executable = os.path.join(temporary.name, 'gh.exe')
        with open(self.executable, 'w'):
            pass
        os.chmod(self.executable, 0o755)

    def test_windows_launches_use_safe_executable_for_stdin_and_normal_commands(self):
        executable = r'C:\installed tools\gh.exe'
        for module in (postgresql, rdbms):
            for input_data in (None, b''):
                with self.subTest(module=module.__name__, input_data=input_data), \
                        patch.object(sys, 'platform', 'win32'), \
                        patch.object(postgresql, 'is_windows', return_value=True), \
                        patch.object(module.os, 'path', ntpath), \
                        patch.object(ntpath, 'isfile', return_value=True), \
                        patch.object(ntpath, 'samefile', return_value=False), \
                        patch.object(module.os, 'access', return_value=True), \
                        patch.object(module, 'get_safe_executable_path', return_value=executable) as resolve, \
                        patch.object(module.subprocess, 'run', return_value=Mock(returncode=0)) as run, \
                        patch.object(module.subprocess, 'Popen', return_value=Mock(returncode=0)) as popen:
                    command = ['gh', 'secret', 'set', 'TEST', '--repo', 'owner/repo']
                    original = list(command)
                    module.run_subprocess(command, input_data=input_data)
                    resolve.assert_called_once_with('gh.exe')
                    if input_data is None:
                        kwargs = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        if module is postgresql:
                            kwargs['shell'] = False
                        popen.assert_called_once_with(
                            [executable] + original[1:], **kwargs)
                        run.assert_not_called()
                    else:
                        run.assert_called_once_with(
                            [executable] + original[1:], input=b'',
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        popen.assert_not_called()
                    self.assertEqual(command, original)

    def test_missing_windows_tool_never_launches_bare_name(self):
        for module in (postgresql, rdbms):
            with self.subTest(module=module.__name__), \
                    patch.object(sys, 'platform', 'win32'), \
                    patch.object(postgresql, 'is_windows', return_value=True), \
                    patch.object(module, 'get_safe_executable_path', return_value=None), \
                    patch.object(module.subprocess, 'run') as run, \
                    patch.object(module.subprocess, 'Popen') as popen:
                with self.assertRaises(FileNotFoundError):
                    module.run_subprocess(['gh', 'auth', 'login'])
                with self.assertRaises(FileNotFoundError):
                    module.run_subprocess(['gh', 'secret', 'set', 'TEST'], input_data=b'')
                with self.assertRaises(FileNotFoundError):
                    module.run_cmd(['gh', 'auth', 'status'], capture_output=True)
                run.assert_not_called()
                popen.assert_not_called()

    def test_login_queries_use_resolved_executable(self):
        executable = self.executable
        for commands, module in ((postgresql_commands, postgresql), (rdbms_commands, rdbms)):
            with self.subTest(module=commands.__name__), \
                    patch.object(module, 'resolve_executable', return_value=executable), \
                    patch.object(postgresql_commands, 'resolve_executable', return_value=executable), \
                    patch.object(module, 'core_run_cmd', return_value=Mock(returncode=0)) as run:
                commands.gitcli_check_and_login()
                self.assertEqual(run.call_args_list, [
                    unittest.mock.call([executable], capture_output=True),
                    unittest.mock.call([executable, 'auth', 'status'], capture_output=True),
                ])


if __name__ == '__main__':
    unittest.main()
